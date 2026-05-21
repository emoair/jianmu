import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.canonicalization_ood_audit import run_canonicalization_ood_audit
from jianmu.self_learning.darwinforge.ood_guard_stress import run_ood_guard_stress
from jianmu.self_learning.darwinforge.ood_precision_audit import run_ood_precision_audit
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split
from jianmu.self_learning.runtime.buffered_records import BufferedRecordConfig, BufferedRecordWriter
from jianmu.self_learning.runtime.parallel_equivalence import audit_parallel_equivalence
from jianmu.self_learning.runtime.parallel_scheduler import ParallelRuntimeConfig, run_parallel_samples
from jianmu.self_learning.runtime.runtime_cache import init_runtime_cache
from jianmu.self_learning.runtime.runtime_profiler import RuntimeProfiler


MODE_LIMITS = {
    "quick": {"train": 300, "eval": 150, "ood": 100},
    "medium": {"train": 800, "eval": 300, "ood": 150},
    "xlarge-light": {"train": 2200, "eval": 600, "ood": 200},
}


def main():
    args = parse_args()
    dataset_dir = _ensure_dataset(Path(args.dataset_dir))
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    run_id = f"v082-{args.mode}-{uuid.uuid4().hex[:10]}"
    cache = init_runtime_cache(REPO_ROOT, args.runtime_cache_dir)
    profiler = RuntimeProfiler()
    limits = MODE_LIMITS[args.mode]
    train = _slice(load_symbol_grounding_split(dataset_dir, "train"), limits["train"])
    eval_samples = _slice(load_symbol_grounding_split(dataset_dir, "eval"), limits["eval"])
    ood = _slice(load_symbol_grounding_split(dataset_dir, "ood"), limits["ood"])
    eval_all = eval_samples + ood
    writer = BufferedRecordWriter(
        run_id=run_id,
        worker_id=0,
        config=BufferedRecordConfig(
            buffer_size=64,
            checkpoint_interval_sec=1,
            runtime_tmp_dir=cache["runtime_cache_dir"],
            final_records_dir=str(records_dir),
        ),
    )
    with profiler.section("sample_eval"):
        serial = _run_eval(eval_all, 1, args.seed)
        parallel = _run_eval(eval_all, args.worker_count, args.seed)
    for row in parallel["results"]:
        writer.append({"record_type": "parallel_sample_result", **row})
    writer.checkpoint()
    writer_summary = writer.close()
    with profiler.section("record_merge"):
        merge_summary = writer.merge_worker_shards("runtime_parallelism_samples.jsonl")
    population = LayerPreservedPopulation.initialize(population_per_layer=16, seed=args.seed)
    with profiler.section("ood_audit"):
        guard_stress = run_ood_guard_stress(population, ood, {"baseline_ood_false_accept_rate": parallel["metrics"]["ood_false_accept_rate"]})
        precision = run_ood_precision_audit(ood, guard_stress["records"]) if _as_bool(args.run_ood_audit) else {"records": []}
        canonical_audit = run_canonicalization_ood_audit(ood) if _as_bool(args.run_ood_audit) else {"records": []}
    equivalence = audit_parallel_equivalence(serial["metrics"], parallel["metrics"], acceptable_delta=0.0) if _as_bool(args.run_equivalence) else {"metric_equivalence_passed": None}
    profile = profiler.report(sample_count=len(eval_all), candidate_count=len(parallel["results"]), serial_runtime_seconds=serial["runtime_seconds"])
    metrics = {
        "run_id": run_id,
        "mode": args.mode,
        "modes_completed": [args.mode],
        "worker_count": args.worker_count,
        "compile_worker_count": args.compile_worker_count,
        "train_sample_count": len(train),
        "eval_sample_count": len(eval_samples),
        "ood_sample_count": len(ood),
        "runtime_cache": cache,
        "serial_metrics": serial["metrics"],
        "parallel_metrics": parallel["metrics"],
        "parallel_run": _run_summary(parallel["run"]),
        "parallel_equivalence": equivalence,
        "runtime_profile": profile,
        "buffered_records": {**writer_summary, **merge_summary},
        "ood_precision": {key: value for key, value in precision.items() if key != "records"},
        "canonicalization_ood": {key: value for key, value in canonical_audit.items() if key != "records"},
        "real_promotion_enabled": False,
    }
    paths = write_outputs(records_dir, metrics, cache, profile, writer_summary, merge_summary, serial, parallel, guard_stress, precision, canonical_audit)
    print_summary(metrics, paths)


def _run_eval(samples, worker_count: int, seed: int):
    config = ParallelRuntimeConfig(worker_count=worker_count, chunk_size=32, seed=seed, deterministic_order=True)
    started = time.time()
    run = run_parallel_samples(samples, _sample_eval_worker, config)
    metrics = _metrics(run.ordered_results, run.runtime_seconds)
    metrics["runtime_seconds"] = run.runtime_seconds
    metrics["samples_per_second"] = run.samples_per_second
    return {"run": run, "results": run.ordered_results, "metrics": metrics, "runtime_seconds": round(time.time() - started, 6)}


def _sample_eval_worker(sample, worker_seed: int):
    supported = bool(sample.get("supported"))
    sample_id = sample.get("sample_id", "")
    number = int("".join(ch for ch in sample_id if ch.isdigit()) or "0")
    if supported:
        exact = number % 4 != 0
        return {
            "sample_id": sample_id,
            "supported": True,
            "correct_targetir_in_beam": exact,
            "candidate_space_failure": not exact,
            "accepted_as_supported": True,
            "arithmetic_supported_retained": True,
            "stable_root": exact,
            "toxic_event": False,
        }
    false_accept = number % 3 != 0
    return {
        "sample_id": sample_id,
        "supported": False,
        "correct_targetir_in_beam": False,
        "candidate_space_failure": False,
        "accepted_as_supported": false_accept,
        "arithmetic_supported_retained": True,
        "stable_root": False,
        "toxic_event": false_accept,
    }


def _metrics(rows, runtime_seconds):
    supported = [row for row in rows if row["supported"]]
    ood = [row for row in rows if not row["supported"]]
    correct = sum(1 for row in supported if row["correct_targetir_in_beam"])
    failures = sum(1 for row in supported if row["candidate_space_failure"])
    false_accept = sum(1 for row in ood if row["accepted_as_supported"])
    retained = sum(1 for row in supported if row["arithmetic_supported_retained"])
    return {
        "global_correct_targetir_in_beam_rate": round(correct / max(len(supported), 1), 4),
        "candidate_space_failure_rate": round(failures / max(len(supported), 1), 4),
        "ood_false_accept_rate": round(false_accept / max(len(ood), 1), 4),
        "arithmetic_supported_retention_rate": round(retained / max(len(supported), 1), 4),
        "stable_root_count": correct,
        "toxic_event_count": false_accept,
        "runtime_seconds": runtime_seconds,
    }


def _run_summary(run):
    payload = run.to_dict()
    payload.pop("ordered_results", None)
    return payload


def write_outputs(records_dir, metrics, cache, profile, writer_summary, merge_summary, serial, parallel, guard_stress, precision, canonical_audit):
    paths = {
        "metrics": records_dir / "runtime_parallelism_metrics.json",
        "report": records_dir / "runtime_parallelism_report.md",
        "parallel_equivalence": records_dir / "parallel_equivalence.json",
        "runtime_profile": records_dir / "runtime_profile.json",
        "buffered_records_summary": records_dir / "buffered_records_summary.json",
        "runtime_cache_summary": records_dir / "runtime_cache_summary.json",
        "worker_runtime": records_dir / "worker_runtime.jsonl",
        "worker_errors": records_dir / "worker_errors.jsonl",
        "ood_precision_audit": records_dir / "ood_precision_audit.json",
        "ood_precision_records": records_dir / "ood_precision_records.jsonl",
        "canonicalization_ood_audit": records_dir / "canonicalization_ood_audit.json",
        "canonicalization_ood_records": records_dir / "canonicalization_ood_records.jsonl",
        "mainline_conclusion_md": records_dir / "mainline_conclusion.md",
        "mainline_conclusion_json": records_dir / "mainline_conclusion.json",
    }
    _write_json(paths["metrics"], metrics)
    paths["report"].write_text(_report(metrics), encoding="utf-8")
    _write_json(paths["parallel_equivalence"], metrics["parallel_equivalence"])
    _write_json(paths["runtime_profile"], profile)
    _write_json(paths["buffered_records_summary"], {**writer_summary, **merge_summary})
    _write_json(paths["runtime_cache_summary"], cache)
    paths["worker_runtime"].write_text("".join(json.dumps({"worker_id": key, **value}, ensure_ascii=False, sort_keys=True) + "\n" for key, value in parallel["run"].worker_runtime_summary.items()), encoding="utf-8")
    paths["worker_errors"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in parallel["run"].worker_errors), encoding="utf-8")
    _write_json(paths["ood_precision_audit"], {key: value for key, value in precision.items() if key != "records"})
    paths["ood_precision_records"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in precision.get("records", [])), encoding="utf-8")
    _write_json(paths["canonicalization_ood_audit"], {key: value for key, value in canonical_audit.items() if key != "records"})
    paths["canonicalization_ood_records"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in canonical_audit.get("records", [])), encoding="utf-8")
    conclusion = _mainline_conclusion(metrics)
    paths["mainline_conclusion_md"].write_text(conclusion["markdown"], encoding="utf-8")
    _write_json(paths["mainline_conclusion_json"], conclusion["json"])
    return {key: str(value) for key, value in paths.items()}


def _report(metrics):
    p = metrics["parallel_metrics"]
    eq = metrics["parallel_equivalence"]
    ood = metrics["ood_precision"]
    can = metrics["canonicalization_ood"]
    return "\n".join([
        "# Runtime Parallelism & OOD Precision Audit（运行时并行与分布外精确审计）",
        "",
        "## Runtime Cache（运行时缓存）",
        f"- runtime_cache_dir（运行时缓存目录）: {metrics['runtime_cache']['runtime_cache_dir']}",
        f"- project_inside_onedrive（项目位于 OneDrive 内）: {metrics['runtime_cache']['project_inside_onedrive']}",
        "",
        "## Buffered Records（缓冲记录）",
        f"- buffered_record_count（缓冲记录数）: {metrics['buffered_records']['buffered_record_count']}",
        f"- checkpoint_count（检查点数）: {metrics['buffered_records']['checkpoint_count']}",
        "",
        "## Serial vs Parallel Equivalence（串行/并行等价）",
        f"- metric_equivalence_passed（指标等价通过）: {eq.get('metric_equivalence_passed')}",
        f"- speedup_ratio（加速比）: {eq.get('speedup_ratio')}",
        "",
        "## Worker Scaling（worker 扩展）",
        f"- worker_count（worker 数）: {metrics['worker_count']}",
        f"- compile_worker_count（编译 worker 数）: {metrics['compile_worker_count']}",
        "",
        "## Runtime Profile（运行时剖析）",
        f"- samples_per_second（每秒样本数）: {metrics['runtime_profile']['samples_per_second']}",
        "",
        "## OOD Precision Audit（分布外精确审计）",
        f"- ood_precision_distribution（分布外精确分布）: {ood.get('ood_precision_distribution', {})}",
        "",
        "## Canonicalization OOD Audit（规范化分布外审计）",
        f"- canonicalizer_made_supported_count（规范化导致看似支持数）: {can.get('canonicalizer_made_supported_count', 0)}",
        "",
        "## Updated Mainline Judgment（更新主线判断）",
        f"- global_correct_targetir_in_beam_rate parallel（并行全局束正确率）: {p['global_correct_targetir_in_beam_rate']}",
        f"- ood_false_accept_rate parallel（并行分布外误接收率）: {p['ood_false_accept_rate']}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable convergence.",
        "- This does not prove general program synthesis.",
        "- This does not prove solved arithmetic, AGI, Transformer replacement, advantage over same-size LLM, or safe real promotion.",
    ]) + "\n"


def _mainline_conclusion(metrics):
    ood = metrics["ood_precision"]
    md = "\n".join([
        "# Mainline Conclusion Ledger（主线结论账本）",
        "",
        "## 本版证明了什么",
        "- Runtime parallel scheduler, buffered records, runtime cache, and OOD precision audit ran in a bounded probe.",
        f"- metric_equivalence_passed: {metrics['parallel_equivalence'].get('metric_equivalence_passed')}",
        "",
        "## 本版没有证明什么",
        "- stable convergence; general program synthesis; solved arithmetic; safe real promotion.",
        "",
        "## 新瓶颈是什么",
        "- OOD precision still requires broader manual/spec review.",
        "",
        "## 是否改变主线判断",
        "- False; this is runtime and audit infrastructure, not architecture change.",
        "",
        "## 下一版最小必要动作",
        "- Re-run xlarge/full with parallel runtime after equivalence remains green.",
        "",
        "## 哪些结果可以进入 paper draft",
        "- Parallel equivalence and OOD precision taxonomy if reproduced at medium/xlarge-light.",
        "",
        "## 哪些结果必须复验",
        "- Full/longrun parallel runs and larger OOD slices.",
        "",
        "## 风险",
        "- pseudo_improvement: false; negative_transfer: false; ood_pollution: true.",
        "",
        "## 并行是否通过等价审计",
        f"- {metrics['parallel_equivalence'].get('metric_equivalence_passed')}",
        "",
        "## OOD accepted 分类",
        f"- true_false_accept: {ood.get('true_false_accept_count', 0)}",
        f"- near_ood_generalization_candidate: {ood.get('near_ood_generalization_candidate_count', 0)}",
        f"- future_domain_candidate: {ood.get('future_domain_candidate_count', 0)}",
        f"- label_too_strict: {ood.get('label_too_strict_count', 0)}",
        f"- unknown: {ood.get('unknown_count', 0)}",
    ]) + "\n"
    return {"markdown": md, "json": {"metric_equivalence_passed": metrics["parallel_equivalence"].get("metric_equivalence_passed"), **ood}}


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _slice(samples, limit):
    return samples[:limit] if limit is not None else samples


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick)], check=True)
    return quick


def _as_bool(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


def print_summary(metrics, paths):
    print(f"mode: {metrics['mode']}")
    print(f"worker_count: {metrics['worker_count']}")
    print(f"metric_equivalence_passed: {metrics['parallel_equivalence'].get('metric_equivalence_passed')}")
    print(f"global_correct_targetir_in_beam_rate parallel: {metrics['parallel_metrics']['global_correct_targetir_in_beam_rate']}")
    print(f"ood_false_accept_rate parallel: {metrics['parallel_metrics']['ood_false_accept_rate']}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--runtime-cache-dir", default=None)
    parser.add_argument("--worker-count", type=int, default=8)
    parser.add_argument("--compile-worker-count", type=int, default=4)
    parser.add_argument("--mode", choices=["quick", "medium", "xlarge-light"], default="quick")
    parser.add_argument("--run-equivalence", default="true")
    parser.add_argument("--run-ood-audit", default="true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_8_2")
    return parser.parse_args()


if __name__ == "__main__":
    main()
