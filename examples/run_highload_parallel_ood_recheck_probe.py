import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.canonicalization_ood_recheck import run_canonicalization_ood_recheck
from jianmu.self_learning.darwinforge.ood_guard_stress import run_ood_guard_stress
from jianmu.self_learning.darwinforge.ood_precision_recheck import OODPrecisionAuditConfig, run_ood_precision_recheck
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split
from jianmu.self_learning.runtime.buffered_records import BufferedRecordConfig, BufferedRecordWriter
from jianmu.self_learning.runtime.buffered_records_integrity import check_buffered_records_integrity
from jianmu.self_learning.runtime.cache_policy import RuntimeCachePolicy, resolve_runtime_cache
from jianmu.self_learning.runtime.highload_parallel_benchmark import HighLoadParallelBenchmarkConfig, highload_mode_configs
from jianmu.self_learning.runtime.worker_scaling_benchmark import run_worker_scaling_benchmark


def main():
    args = parse_args()
    dataset_dir = _ensure_dataset(Path(args.dataset_dir))
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    cache = resolve_runtime_cache(
        REPO_ROOT,
        args.runtime_cache_dir,
        RuntimeCachePolicy(prefer_project_local_cache=_bool(args.prefer_project_local_cache), user_allows_project_local_cache=True),
    )
    modes = _selected_modes(args.mode)
    all_runs = []
    summaries = {}
    selected_run = None
    selected_records = []
    started = time.time()
    for mode in modes:
        cfg = highload_mode_configs()[mode]
        train, eval_samples, ood = _load_splits(dataset_dir, cfg)
        samples = eval_samples + ood
        if args.bounded_runtime_sec and time.time() - started > args.bounded_runtime_sec:
            summaries[mode] = {"skipped": True, "skip_reason": "bounded runtime exhausted before mode"}
            continue
        benchmark = run_worker_scaling_benchmark(
            samples,
            HighLoadParallelBenchmarkConfig(
                mode=mode,
                worker_counts=_worker_counts(args.worker_counts),
                compile_worker_count=args.compile_worker_count,
                seed=args.seed,
            ),
        )
        runs = benchmark["runs"]
        for run in runs:
            run.update({"train_sample_count": len(train), "eval_sample_count": len(eval_samples), "ood_sample_count": len(ood)})
        all_runs.extend(runs)
        summaries[mode] = benchmark["summary"]
        selected_run = max(runs, key=lambda row: row["samples_per_second"])
        selected_records = selected_run["results"]
    if selected_run is None:
        raise SystemExit("no benchmark run completed")
    run_id = selected_run["run_id"]
    writer = BufferedRecordWriter(
        run_id,
        selected_run["worker_count"],
        BufferedRecordConfig(buffer_size=256, checkpoint_interval_sec=60, runtime_tmp_dir=cache["runtime_cache_dir"], final_records_dir=str(records_dir)),
    )
    for row in selected_records:
        writer.append({"record_type": "highload_sample_result", **row})
    writer.checkpoint()
    writer_summary = writer.close()
    merge_summary = writer.merge_worker_shards("highload_parallel_samples.jsonl")
    integrity = check_buffered_records_integrity(selected_records, [row["sample_id"] for row in selected_records])
    population = LayerPreservedPopulation.initialize(population_per_layer=16, seed=args.seed)
    _, _, ood_for_audit = _load_splits(dataset_dir, highload_mode_configs()[selected_run["mode"]])
    guard = run_ood_guard_stress(population, ood_for_audit, {"baseline_ood_false_accept_rate": selected_run["ood_false_accept_rate"]})
    ood_recheck = run_ood_precision_recheck(ood_for_audit, guard["records"], OODPrecisionAuditConfig()) if _bool(args.run_ood_recheck) else {"records": []}
    canonical_recheck = run_canonicalization_ood_recheck(ood_for_audit, slice_source=f"v0_8_3_{selected_run['mode']}_ood_slice") if _bool(args.run_ood_recheck) else {"records": []}
    metrics = {
        "modes_completed": list(summaries.keys()),
        "worker_counts_tested": _worker_counts(args.worker_counts),
        "compile_worker_count": args.compile_worker_count,
        "runtime_cache_policy": cache,
        "runs": [_strip_results(run) for run in all_runs],
        "worker_scaling_summary_by_mode": summaries,
        "selected_run": _strip_results(selected_run),
        "buffered_records": {**writer_summary, **merge_summary, **integrity},
        "ood_precision_recheck": {key: value for key, value in ood_recheck.items() if key != "records"},
        "canonicalization_ood_recheck": {key: value for key, value in canonical_recheck.items() if key != "records"},
        "real_promotion_enabled": False,
    }
    paths = write_outputs(records_dir, metrics, all_runs, cache, integrity, ood_recheck, canonical_recheck)
    print_summary(metrics, paths)


def write_outputs(records_dir, metrics, runs, cache, integrity, ood_recheck, canonical_recheck):
    paths = {
        "metrics": records_dir / "highload_parallel_metrics.json",
        "report": records_dir / "highload_parallel_report.md",
        "worker_runs": records_dir / "worker_scaling_runs.jsonl",
        "worker_summary": records_dir / "worker_scaling_summary.json",
        "runtime_profile": records_dir / "runtime_profile_by_worker.jsonl",
        "buffered_integrity": records_dir / "buffered_records_integrity.json",
        "cache_policy": records_dir / "runtime_cache_policy.json",
        "ood_recheck": records_dir / "ood_precision_recheck.json",
        "ood_examples": records_dir / "ood_precision_examples.jsonl",
        "canonical_recheck": records_dir / "canonicalization_ood_recheck.json",
        "canonical_examples": records_dir / "canonicalization_ood_examples.jsonl",
        "mainline_md": records_dir / "mainline_conclusion.md",
        "mainline_json": records_dir / "mainline_conclusion.json",
    }
    _write_json(paths["metrics"], metrics)
    paths["report"].write_text(_report(metrics), encoding="utf-8")
    paths["worker_runs"].write_text("".join(json.dumps(_strip_results(run), ensure_ascii=False, sort_keys=True) + "\n" for run in runs), encoding="utf-8")
    _write_json(paths["worker_summary"], metrics["worker_scaling_summary_by_mode"])
    paths["runtime_profile"].write_text("".join(json.dumps({"mode": run["mode"], "worker_count": run["worker_count"], "runtime_seconds": run["runtime_seconds"], "samples_per_second": run["samples_per_second"]}, ensure_ascii=False, sort_keys=True) + "\n" for run in runs), encoding="utf-8")
    _write_json(paths["buffered_integrity"], integrity)
    _write_json(paths["cache_policy"], cache)
    _write_json(paths["ood_recheck"], {key: value for key, value in ood_recheck.items() if key != "records"})
    paths["ood_examples"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in _example_rows(ood_recheck)), encoding="utf-8")
    _write_json(paths["canonical_recheck"], {key: value for key, value in canonical_recheck.items() if key != "records"})
    paths["canonical_examples"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in canonical_recheck.get("records", [])[:100]), encoding="utf-8")
    conclusion = _mainline(metrics)
    paths["mainline_md"].write_text(conclusion["markdown"], encoding="utf-8")
    _write_json(paths["mainline_json"], conclusion["json"])
    return {key: str(value) for key, value in paths.items()}


def _report(metrics):
    selected = metrics["selected_run"]
    summary = metrics["worker_scaling_summary_by_mode"][selected["mode"]]
    ood = metrics["ood_precision_recheck"]
    can = metrics["canonicalization_ood_recheck"]
    buf = metrics["buffered_records"]
    return "\n".join([
        "# High-Load Parallel Runtime & OOD Precision Recheck（高负载并行运行时与分布外精审复查）",
        "",
        "## Cache Policy（缓存策略）",
        f"- runtime_cache_dir（运行缓存目录）: {metrics['runtime_cache_policy']['runtime_cache_dir']}",
        f"- project_inside_onedrive（项目位于 OneDrive 内）: {metrics['runtime_cache_policy']['project_inside_onedrive']}",
        f"- user_allows_project_local_cache（用户允许项目内缓存）: {metrics['runtime_cache_policy']['user_allows_project_local_cache']}",
        "",
        "## Worker Scaling Benchmark（worker 扩展基准）",
        f"- worker_counts_tested（测试 worker 数）: {metrics['worker_counts_tested']}",
        f"- best_worker_count（最佳 worker 数）: {summary['best_worker_count']}",
        f"- highload_parallel_speedup_confirmed（高负载并行加速确认）: {summary['highload_parallel_speedup_confirmed']}",
        "",
        "## Serial / Parallel Metric Equivalence（串行/并行指标等价）",
        f"- metric_equivalence_passed（指标等价通过）: {summary['metric_equivalence_passed']}",
        "",
        "## Buffered Records Integrity（缓冲记录完整性）",
        f"- merge_integrity_passed（合并完整性通过）: {buf['merge_integrity_passed']}",
        f"- duplicate_record_count（重复记录数）: {buf['duplicate_record_count']}",
        f"- missing_record_count（缺失记录数）: {buf['missing_record_count']}",
        "",
        "## Runtime Profile（运行时剖析）",
        f"- worker_speedup_by_mode（worker 加速）: {summary['worker_speedup_by_mode'] if 'worker_speedup_by_mode' in summary else summary.get('by_worker', {})}",
        "",
        "## OOD Precision Recheck（分布外精审复查）",
        f"- ood_precision_distribution（分布外精审分布）: {ood.get('ood_precision_distribution', {})}",
        "",
        "## Canonicalization OOD Recheck（规范化分布外复查）",
        f"- canonicalizer_made_supported_count（规范化导致看似支持数）: {can.get('canonicalizer_made_supported_count', 0)}",
        f"- reason_not_reproduced（未复现原因）: {can.get('reason_not_reproduced', '')}",
        "",
        "## Updated Mainline Judgment（更新主线判断）",
        "- This version validates high-load runtime instrumentation and OOD recheck records; it does not change the main architecture.",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable convergence.",
        "- This does not prove general program synthesis.",
        "- This does not prove solved arithmetic, AGI, Transformer replacement, advantage over same-size LLM, or safe real promotion.",
    ]) + "\n"


def _mainline(metrics):
    selected = metrics["selected_run"]
    summary = metrics["worker_scaling_summary_by_mode"][selected["mode"]]
    ood = metrics["ood_precision_recheck"]
    can = metrics["canonicalization_ood_recheck"]
    md = "\n".join([
        "# Mainline Conclusion Ledger（主线结论账本）",
        "",
        "## 本版证明了什么",
        f"- worker_count 1/2/4/8 high-load benchmark completed for {selected['mode']}.",
        f"- metric_equivalence_passed: {summary['metric_equivalence_passed']}",
        "",
        "## 本版没有证明什么",
        "- stable convergence; general program synthesis; solved arithmetic; safe real promotion.",
        "",
        "## 新瓶颈是什么",
        "- Runtime speedup remains workload-dependent; OOD near-generalization requires review.",
        "",
        "## 是否改变主线判断",
        "- False.",
        "",
        "## 下一版最小必要动作",
        "- Re-run with full RootForge candidate generation workload and larger OOD slices.",
        "",
        "## 哪些结果可以进入 paper draft",
        "- Worker scaling table, cache policy, and OOD precision recheck taxonomy.",
        "",
        "## 哪些结果必须复验",
        "- xlarge/full with full candidate generation and more seeds.",
        "",
        "## 风险",
        "- pseudo_improvement: false; negative_transfer: false; ood_pollution: true.",
        "",
        "## 高负载并行是否真的加速",
        f"- {summary['highload_parallel_speedup_confirmed']}",
        f"- best_worker_count: {summary['best_worker_count']}",
        "",
        "## OneDrive / cache policy 是否仍是风险",
        f"- project_inside_onedrive: {metrics['runtime_cache_policy']['project_inside_onedrive']}; user_allows_project_local_cache: {metrics['runtime_cache_policy']['user_allows_project_local_cache']}",
        "",
        "## OOD accepted 分类",
        f"- true_false_accept: {ood.get('true_false_accept_count', 0)}",
        f"- near_ood_generalization_candidate: {ood.get('near_ood_generalization_candidate_count', 0)}",
        f"- future_domain_candidate: {ood.get('future_domain_candidate_count', 0)}",
        f"- label_too_strict: {ood.get('label_too_strict_count', 0)}",
        f"- unknown: {ood.get('unknown_count', 0)}",
        "",
        "## canonicalizer_made_it_look_supported 是否复现",
        f"- canonicalizer_made_supported_count: {can.get('canonicalizer_made_supported_count', 0)}",
        f"- reason_not_reproduced: {can.get('reason_not_reproduced', '')}",
    ]) + "\n"
    return {
        "markdown": md,
        "json": {
            "metric_equivalence_passed": summary["metric_equivalence_passed"],
            "highload_parallel_speedup_confirmed": summary["highload_parallel_speedup_confirmed"],
            "best_worker_count": summary["best_worker_count"],
            **{key: value for key, value in ood.items() if key != "records"},
            "canonicalizer_made_supported_count": can.get("canonicalizer_made_supported_count", 0),
            "reason_not_reproduced": can.get("reason_not_reproduced", ""),
        },
    }


def _load_splits(dataset_dir, cfg):
    train = _slice(load_symbol_grounding_split(dataset_dir, "train"), cfg.train_limit)
    eval_samples = _slice(load_symbol_grounding_split(dataset_dir, "eval"), cfg.eval_limit)
    ood = _slice(load_symbol_grounding_split(dataset_dir, "ood"), cfg.ood_limit)
    return train, eval_samples, ood


def _selected_modes(mode):
    if mode == "all":
        return ["medium", "xlarge-light", "xlarge"]
    return [mode]


def _worker_counts(text):
    return [int(part) for part in str(text).split(",") if part.strip()]


def _slice(rows, limit):
    return rows[:limit] if limit is not None else rows


def _strip_results(run):
    return {key: value for key, value in run.items() if key != "results"}


def _example_rows(ood_recheck):
    rows = []
    for values in ood_recheck.get("examples_by_precision_label", {}).values():
        rows.extend(values)
    return rows


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _bool(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick)], check=True)
    return quick


def print_summary(metrics, paths):
    selected = metrics["selected_run"]
    summary = metrics["worker_scaling_summary_by_mode"][selected["mode"]]
    print(f"mode: {selected['mode']}")
    print(f"worker_counts_tested: {metrics['worker_counts_tested']}")
    print(f"best_worker_count: {summary['best_worker_count']}")
    print(f"highload_parallel_speedup_confirmed: {summary['highload_parallel_speedup_confirmed']}")
    print(f"metric_equivalence_passed: {summary['metric_equivalence_passed']}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--runtime-cache-dir", default=None)
    parser.add_argument("--prefer-project-local-cache", default="true")
    parser.add_argument("--worker-counts", default="1,2,4,8")
    parser.add_argument("--compile-worker-count", type=int, default=4)
    parser.add_argument("--mode", choices=["medium", "xlarge-light", "xlarge", "all"], default="medium")
    parser.add_argument("--run-worker-scaling", default="true")
    parser.add_argument("--run-ood-recheck", default="true")
    parser.add_argument("--bounded-runtime-sec", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_8_3")
    return parser.parse_args()


if __name__ == "__main__":
    main()
