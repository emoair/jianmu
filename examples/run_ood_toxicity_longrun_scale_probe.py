import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.run_colony_scale_stress_probe import run_scale
from jianmu.self_learning.darwinforge.colony_scale_stress import new_run_id
from jianmu.self_learning.darwinforge.longrun_scale_probe import longrun_scale_configs, should_skip_longrun
from jianmu.self_learning.darwinforge.ood_guard_stress import run_ood_guard_stress
from jianmu.self_learning.darwinforge.ood_retention_balance import evaluate_guard_candidate, summarize_guard_balance
from jianmu.self_learning.darwinforge.ood_toxicity_taxonomy import summarize_ood_taxonomy
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.scale_bottleneck_diagnosis import diagnose_scale_bottlenecks
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    dataset_dir = _ensure_dataset(Path(args.dataset_dir))
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    configs = longrun_scale_configs(seed=args.seed)
    attempted = _modes_for(args.mode)
    scale_runs = []
    guard_records = []
    guard_results = []
    guard_stress = _empty_guard_stress()
    for mode in attempted:
        skip_reason = should_skip_longrun(mode, args.bounded_runtime_sec, allow_expensive=args.allow_expensive)
        run_id = new_run_id(mode)
        if skip_reason:
            scale_runs.append({"mode": mode, "scale_label": mode, "run_id": run_id, "completed": False, "partial": False, "skipped": True, "skip_reason": skip_reason})
            continue
        started = time.time()
        scale_run, _ = run_scale(dataset_dir, configs[mode], run_id)
        scale_run.update({"mode": mode, "completed": True, "partial": False, "skip_reason": ""})
        if args.bounded_runtime_sec and time.time() - started > args.bounded_runtime_sec:
            scale_run["partial"] = True
            scale_run["skip_reason"] = "completed after bounded runtime target（超过受限运行目标后完成）"
        scale_runs.append(scale_run)
        ood_samples = _slice(load_symbol_grounding_split(dataset_dir, "ood"), configs[mode].ood_limit)
        population = LayerPreservedPopulation.initialize(population_per_layer=configs[mode].population_per_layer, seed=args.seed)
        guard_stress = run_ood_guard_stress(population, ood_samples, {"baseline_ood_false_accept_rate": scale_run.get("ood_false_accept_after_shadow", 0.67)})
        for row in guard_stress.get("records", []):
            row["mode"] = mode
            row["run_id"] = run_id
        guard_records.extend(guard_stress.get("records", []))
        guard_results.extend(_guard_candidates(args, population, scale_run, ood_samples))
    representative_run = next((run for run in reversed(scale_runs) if run.get("completed")), scale_runs[-1])
    guard_stress = {**guard_stress, "records": guard_records}
    diagnosis = _diagnose(representative_run, guard_stress, guard_results)
    metrics = {
        "modes_attempted": attempted,
        "modes_completed": [run["mode"] for run in scale_runs if run.get("completed")],
        "partial_or_skipped": {run["mode"]: run.get("skip_reason") for run in scale_runs if run.get("skipped") or run.get("partial")},
        "runs": scale_runs,
        "run": representative_run,
        "ood_taxonomy": {key: value for key, value in guard_stress.items() if key.endswith("_by_class") or key in {"ood_class_distribution", "toxic_event_by_class", "rejection_layer_by_class"}},
        "ood_guard_stress": {key: value for key, value in guard_stress.items() if key != "records"},
        **summarize_guard_balance(guard_results),
        **diagnosis,
    }
    paths = write_outputs(records_dir, metrics, scale_runs, guard_stress, guard_results, diagnosis)
    print_summary(metrics, paths)


def _guard_candidates(args, population, scale_run, ood_samples):
    if str(args.enable_guard_candidates).lower() != "true":
        return []
    base = {
        "ood_false_accept_before": scale_run.get("ood_false_accept_after_shadow", 0.0),
        "ood_false_accept_after": max(0.0, scale_run.get("ood_false_accept_after_shadow", 0.0) - 0.1),
        "arithmetic_supported_retention_before": scale_run.get("arithmetic_supported_retention_rate", 1.0),
        "arithmetic_supported_retention_after": scale_run.get("arithmetic_supported_retention_rate", 1.0),
        "global_beam_before": scale_run.get("global_correct_targetir_in_beam_rate_after_shadow", 0.0),
        "global_beam_after": scale_run.get("global_correct_targetir_in_beam_rate_after_shadow", 0.0),
        "toxic_event_before": scale_run.get("toxic_event_count", 0),
        "toxic_event_after": max(0, scale_run.get("toxic_event_count", 0) - max(1, int(len(ood_samples) * 0.05))),
        "update_type": "shadow_ood_guard_candidate",
    }
    rollback = dict(base, arithmetic_supported_retention_after=base["arithmetic_supported_retention_before"] - 0.05, update_type="retention_regression_probe")
    return [
        evaluate_guard_candidate(population, base, [], ood_samples),
        evaluate_guard_candidate(population, rollback, [], ood_samples),
    ]


def _diagnose(scale_run, guard_stress, guard_results):
    scale_diag = diagnose_scale_bottlenecks([scale_run] if not scale_run.get("skipped") else [])
    guard_summary = summarize_guard_balance(guard_results)
    guard_limited = guard_summary.get("guard_candidate_accepted_count", 0) == 0 and guard_stress.get("ood_false_accept_rate", 0.0) > 0.25
    summary = scale_diag.get("diagnosis_summary", "")
    if guard_limited:
        summary += " guard_limited（守卫受限） signal: guard candidates did not pass rollback-safe gates while OOD toxicity stayed high."
    return {
        "scale_limited_likely": scale_diag.get("scale_limited_likely", False),
        "ood_limited_likely": True if guard_stress.get("ood_false_accept_rate", 0.0) > 0.25 else scale_diag.get("ood_limited_likely", False),
        "guard_limited_likely": guard_limited,
        "routing_limited_likely": scale_diag.get("routing_limited_likely", False),
        "resource_limited_likely": scale_diag.get("resource_limited_likely", False),
        "diagnosis_summary": summary.strip(),
    }


def write_outputs(records_dir, metrics, scale_runs, guard_stress, guard_results, diagnosis):
    paths = {
        "metrics_path": records_dir / "ood_toxicity_longrun_metrics.json",
        "report_path": records_dir / "ood_toxicity_longrun_report.md",
        "taxonomy_path": records_dir / "ood_toxicity_by_class.json",
        "guard_stress_path": records_dir / "ood_guard_stress.jsonl",
        "guard_candidates_path": records_dir / "ood_guard_candidates.jsonl",
        "retention_balance_path": records_dir / "ood_retention_balance.jsonl",
        "longrun_runs_path": records_dir / "longrun_scale_runs.jsonl",
        "runtime_path": records_dir / "longrun_runtime.jsonl",
        "diagnosis_path": records_dir / "longrun_bottleneck_diagnosis.json",
    }
    paths["metrics_path"].write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["report_path"].write_text(report(metrics), encoding="utf-8")
    paths["taxonomy_path"].write_text(json.dumps(metrics["ood_taxonomy"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["guard_stress_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in guard_stress.get("records", [])), encoding="utf-8")
    paths["guard_candidates_path"].write_text("".join(json.dumps(row.get("guard_update", {}), ensure_ascii=False, sort_keys=True) + "\n" for row in guard_results), encoding="utf-8")
    paths["retention_balance_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in guard_results), encoding="utf-8")
    paths["longrun_runs_path"].write_text("".join(json.dumps(run, ensure_ascii=False, sort_keys=True) + "\n" for run in scale_runs), encoding="utf-8")
    paths["runtime_path"].write_text("".join(json.dumps({"mode": run.get("mode"), "run_id": run.get("run_id"), "runtime_seconds": run.get("runtime_seconds", 0.0), "completed": run.get("completed", False), "partial": run.get("partial", False), "skip_reason": run.get("skip_reason", "")}, ensure_ascii=False, sort_keys=True) + "\n" for run in scale_runs), encoding="utf-8")
    paths["diagnosis_path"].write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def report(metrics):
    run = metrics["run"]
    return "\n".join([
        "# OOD Toxicity Stress & Long-Run Scale Probe（分布外毒性压力与长时规模探针） Report（报告）",
        "",
        "## Long-Run Scale Summary（长时规模摘要）",
        f"- modes_attempted（尝试模式）: {metrics.get('modes_attempted')}",
        f"- modes_completed（完成模式）: {metrics.get('modes_completed')}",
        f"- partial_or_skipped（部分或跳过）: {metrics.get('partial_or_skipped')}",
        "",
        "## Global Beam Trend（全局束趋势）",
        f"- global_correct_targetir_in_beam_rate（正确目标中间表示在束内率）: {run.get('global_correct_targetir_in_beam_rate_after_shadow', 0.0)}",
        f"- candidate_space_failure_rate（候选空间失败率）: {run.get('candidate_space_failure_rate_after_shadow', 0.0)}",
        "",
        "## OOD Toxicity Taxonomy（分布外毒性分类）",
        f"- ood_false_accept_by_class（按类误接收）: {metrics['ood_guard_stress'].get('ood_false_accept_by_class', {})}",
        "",
        "## OOD False Accept Analysis（分布外误接收分析）",
        f"- most_common_false_accept_reason（最常见误接收原因）: {metrics['ood_guard_stress'].get('most_common_false_accept_reason', 'none')}",
        "",
        "## Guard / Retention Balance（守卫与保留平衡）",
        f"- guard_candidate_count（守卫候选数）: {metrics.get('guard_candidate_count', 0)}",
        f"- guard_candidate_accepted_count（接受守卫候选数）: {metrics.get('guard_candidate_accepted_count', 0)}",
        f"- arithmetic_supported_retention_after_guard（守卫后算术支持保留率）: {metrics.get('arithmetic_supported_retention_after_guard', 0.0)}",
        "",
        "## Root Colony Lifecycle（根群生命周期）",
        f"- stable_root_count（稳定根数）: {run.get('stable_root_count', 0)}",
        f"- nourished_root_count（有养分根数）: {run.get('nourished_root_count', 0)}",
        "",
        "## Runtime and Resource Cost（运行时间与资源成本）",
        f"- runtime_seconds（运行秒数）: {run.get('runtime_seconds', 0.0)}",
        f"- total_active_roots（总活跃根数）: {run.get('total_active_roots', 0)}",
        "",
        "## Bottleneck Diagnosis（瓶颈诊断）",
        f"- diagnosis_summary（诊断摘要）: {metrics.get('diagnosis_summary', '')}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable RootForge（根铸） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not prove AGI, Transformer replacement, hardware BPU implementation, or solved arithmetic.",
    ]) + "\n"


def _empty_guard_stress():
    return {"records": [], "ood_false_accept_rate": 0.0, "ood_correct_rejection_rate": 0.0, "ood_toxicity_rate": 0.0}


def _modes_for(mode):
    if mode == "large":
        return ["large"]
    if mode == "xlarge":
        return ["large", "xlarge"]
    if mode == "full":
        return ["large", "xlarge", "full"]
    return ["large", "xlarge", "full", "longrun"]


def _slice(samples, limit):
    return samples[:limit] if limit is not None else samples


def _ensure_dataset(dataset_dir):
    if (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        return dataset_dir
    quick = Path("datasets/v0_7_0_quick")
    subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick)], check=True)
    return quick


def print_summary(metrics, paths):
    run = metrics["run"]
    print(f"mode: {run.get('mode')}")
    print(f"completed: {run.get('completed')}")
    print(f"partial: {run.get('partial')}")
    print(f"skip_reason: {run.get('skip_reason')}")
    print(f"ood_false_accept_rate: {metrics['ood_guard_stress'].get('ood_false_accept_rate')}")
    print(f"diagnosis_summary: {metrics.get('diagnosis_summary')}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["large", "xlarge", "full", "longrun"], default="large")
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--bounded-runtime-sec", type=int, default=None)
    parser.add_argument("--enable-guard-candidates", default="true")
    parser.add_argument("--real-promotion", default="false")
    parser.add_argument("--allow-expensive", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_8_1")
    args = parser.parse_args()
    if str(args.real_promotion).lower() == "true":
        raise SystemExit("real promotion is disabled for v0.8.1（v0.8.1 禁止真实晋升）")
    return args


if __name__ == "__main__":
    main()
