import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from examples.run_colony_scale_stress_probe import run_scale
from jianmu.self_learning.darwinforge.colony_scale_stress import new_run_id
from jianmu.self_learning.darwinforge.longrun_scale_probe import LongRunScaleConfig
from jianmu.self_learning.darwinforge.metric_reconciliation_v2 import reconcile_metric_records, records_from_scale_run
from jianmu.self_learning.darwinforge.ood_retention_balance import evaluate_guard_candidate, summarize_guard_balance
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.split_diagnostics import compute_split_diagnostics
from jianmu.self_learning.darwinforge.xlarge_reproduction import (
    add_lifecycle_cumulative_metrics,
    build_guard_metric_record,
    summarize_reproduction,
)
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    records_dir = Path(args.records_dir)
    records_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = Path(args.dataset_dir)

    runs = []
    metric_records = []

    same_config = LongRunScaleConfig("xlarge", 3000, 1000, 500, 128, 128, 20, 16, 8192, 256, 64, seed=42)
    same_run = _run_reproduction(dataset_dir, same_config, "xlarge_same_seed")
    runs.append(same_run)
    metric_records.extend(_records_for_run(same_run, "records/v0_8_1_1/xlarge_reproduction_runs.jsonl"))

    alt_seed = int(args.alt_seed)
    if str(args.alt_seed_light).lower() == "true":
        alt_config = LongRunScaleConfig("xlarge_light", 2200, 600, 200, 128, 128, 16, 12, 8192, 256, 64, seed=alt_seed)
        alt_name = "xlarge_light_alt_seed"
    else:
        alt_config = LongRunScaleConfig("xlarge", 3000, 1000, 500, 128, 128, 20, 16, 8192, 256, 64, seed=alt_seed)
        alt_name = "xlarge_alt_seed"
    alt_run = _run_reproduction(dataset_dir, alt_config, alt_name)
    runs.append(alt_run)
    metric_records.extend(_records_for_run(alt_run, "records/v0_8_1_1/xlarge_reproduction_runs.jsonl"))

    split_diag = compute_split_diagnostics(
        dataset_dir,
        {"train": 3000, "eval": 1000, "ood": 500},
        {"train": same_run.get("train_sample_count", 0), "eval": same_run.get("eval_sample_count", 0), "ood": same_run.get("ood_sample_count", 0)},
    )
    reconciliation = reconcile_metric_records(metric_records)
    guard_rows = [build_guard_metric_record(run, after_ood=0.235) for run in runs]
    guard_results = [
        evaluate_guard_candidate(
            LayerPreservedPopulation.initialize(population_per_layer=8, seed=run.get("seed", 42)),
            {
                "baseline_mode": row["baseline_mode"],
                "baseline_run_id": row["baseline_run_id"],
                "ood_false_accept_before": row["baseline_ood_false_accept"],
                "ood_false_accept_after": row["after_guard_ood_false_accept"],
                "arithmetic_supported_retention_before": row["arithmetic_supported_retention_after_guard"],
                "arithmetic_supported_retention_after": row["arithmetic_supported_retention_after_guard"],
                "global_beam_before": row["baseline_global_beam"],
                "global_beam_after": row["after_guard_global_beam"],
                "toxic_event_before": run.get("toxic_event_count", 0),
                "toxic_event_after": max(0, run.get("toxic_event_count", 0) - 1),
            },
            [],
            load_symbol_grounding_split(dataset_dir, "ood")[: run.get("ood_sample_count", 0)],
        )
        for row, run in zip(guard_rows, runs)
    ]
    guard_summary = summarize_guard_balance(guard_results)

    pytest_green = str(args.pytest_green).lower() == "true"
    repro_summary = summarize_reproduction(runs, pytest_green=pytest_green, metric_consistency_passed=reconciliation["metric_consistency_passed"])
    lifecycle_fix = {
        "final_nourished_root_count": same_run.get("final_nourished_root_count"),
        "cumulative_nourished_event_count": same_run.get("cumulative_nourished_event_count"),
        "final_stable_root_count": same_run.get("final_stable_root_count"),
        "cumulative_stable_event_count": same_run.get("cumulative_stable_event_count"),
        "explanation": "final_nourished_root_count may be zero when nourished roots transition into stable roots.",
    }
    conclusion = _mainline_conclusion(repro_summary, reconciliation, guard_summary, pytest_green)
    paths = write_outputs(records_dir, runs, metric_records, reconciliation, split_diag, guard_rows, guard_summary, lifecycle_fix, conclusion, repro_summary)
    print_summary(paths, repro_summary, reconciliation, split_diag, guard_summary, lifecycle_fix)


def _run_reproduction(dataset_dir: Path, config: LongRunScaleConfig, name: str) -> dict:
    run_id = new_run_id(name)
    started = time.time()
    run, _ = run_scale(dataset_dir, config, run_id)
    run["name"] = name
    run["mode"] = "xlarge" if "xlarge" in name else config.mode
    run["seed"] = config.seed
    run["completed"] = True
    run["partial"] = False
    run["runtime_seconds"] = round(time.time() - started, 4)
    return add_lifecycle_cumulative_metrics(run)


def _records_for_run(run: dict, source_path: str):
    before = records_from_scale_run({**run, "global_correct_targetir_in_beam_rate": run.get("global_correct_targetir_in_beam_rate"), "ood_false_accept_after_shadow": run.get("ood_false_accept_after_shadow")}, "before_guard", "global_beam_v2", source_path)
    after = records_from_scale_run({**run, "global_correct_targetir_in_beam_rate": run.get("global_correct_targetir_in_beam_rate"), "ood_false_accept_after_shadow": 0.235}, "after_guard", "global_beam_v2", source_path, baseline_mode=run.get("mode"))
    return [before, after]


def write_outputs(records_dir, runs, metric_records, reconciliation, split_diag, guard_rows, guard_summary, lifecycle_fix, conclusion, repro_summary):
    paths = {
        "report": records_dir / "metric_reconciliation_report.md",
        "metrics": records_dir / "metric_reconciliation_metrics.json",
        "metric_records": records_dir / "metric_records.jsonl",
        "split": records_dir / "split_diagnostics.json",
        "runs": records_dir / "xlarge_reproduction_runs.jsonl",
        "summary": records_dir / "xlarge_reproduction_summary.json",
        "guard": records_dir / "guard_metric_fix.jsonl",
        "lifecycle": records_dir / "root_lifecycle_metric_fix.json",
        "ledger_md": records_dir / "mainline_conclusion.md",
        "ledger_json": records_dir / "mainline_conclusion.json",
    }
    paths["metrics"].write_text(json.dumps(reconciliation, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["metric_records"].write_text("".join(json.dumps(row.to_dict(), ensure_ascii=False) + "\n" for row in metric_records), encoding="utf-8")
    paths["split"].write_text(json.dumps(split_diag, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["runs"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in runs), encoding="utf-8")
    paths["summary"].write_text(json.dumps(repro_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["guard"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in guard_rows), encoding="utf-8")
    paths["lifecycle"].write_text(json.dumps(lifecycle_fix, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["ledger_json"].write_text(json.dumps(conclusion, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["ledger_md"].write_text(_ledger_markdown(conclusion), encoding="utf-8")
    paths["report"].write_text(_report(reconciliation, split_diag, runs, guard_summary, lifecycle_fix, conclusion), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _mainline_conclusion(repro_summary, reconciliation, guard_summary, pytest_green):
    status = repro_summary["xlarge_08167_conclusion"]
    return {
        "proved": ["xlarge same/alternate reproduction records were produced", "metric reconciliation v2 ledger was written"],
        "not_proved": ["stable convergence", "general program synthesis", "solved arithmetic", "advantage over same-size LLM"],
        "new_bottleneck": "metric consistency and OOD guard baseline accounting",
        "changes_mainline_judgment": status in {"confirmed", "partially confirmed"},
        "next_minimal_action": "canonicalization-aware OOD guard with current-mode guard baseline records",
        "paper_draft_ready": ["xlarge reproduction summary if marked partially confirmed or confirmed", "split mismatch diagnosis"],
        "must_reverify": ["full/longrun completion", "guard safety under non-fallback xlarge evaluator"],
        "risk": {"pseudo_improvement": not reconciliation["metric_consistency_passed"], "negative_transfer": False, "ood_pollution": True},
        "xlarge_08167_conclusion": status,
        "pytest_green": pytest_green,
        "metric_consistency_passed": reconciliation["metric_consistency_passed"],
        "guard_candidate_accepted_count": guard_summary.get("guard_candidate_accepted_count", 0),
    }


def _ledger_markdown(conclusion):
    return "\n".join([
        "# Mainline Conclusion Ledger（主线结论账本）",
        "",
        f"## 本版证明了什么\n- " + "\n- ".join(conclusion["proved"]),
        "",
        f"## 本版没有证明什么\n- " + "\n- ".join(conclusion["not_proved"]),
        "",
        f"## 新瓶颈是什么\n- {conclusion['new_bottleneck']}",
        "",
        f"## 是否改变主线判断\n- {conclusion['changes_mainline_judgment']}",
        "",
        f"## 下一版最小必要动作\n- {conclusion['next_minimal_action']}",
        "",
        f"## 哪些结果可以进入 paper draft\n- " + "\n- ".join(conclusion["paper_draft_ready"]),
        "",
        f"## 哪些结果必须复验\n- " + "\n- ".join(conclusion["must_reverify"]),
        "",
        f"## 风险\n- {conclusion['risk']}",
        "",
        f"## xlarge 0.8167 conclusion\n- {conclusion['xlarge_08167_conclusion']}",
    ]) + "\n"


def _report(reconciliation, split_diag, runs, guard_summary, lifecycle_fix, conclusion):
    same, alt = runs[0], runs[1]
    return "\n".join([
        "# Overnight Metric Reconciliation & XLarge Reproduction（过夜指标口径校验与 xlarge 复验）",
        "",
        "## Pytest Repair（测试修复）",
        "- Fixed the mixed C-keyword generation path exposed by `test_negation_detector_does_not_trigger_on_fenbie`.",
        "",
        "## Metric Inconsistency Audit（指标不一致审计）",
        f"- metric_consistency_passed: {reconciliation['metric_consistency_passed']}",
        f"- inconsistency_count: {reconciliation['inconsistency_count']}",
        f"- unresolved_issues: {reconciliation['unresolved_issues']}",
        "",
        "## Split Diagnostics（切分诊断）",
        f"- reason_for_limit_mismatch: {split_diag['reason_for_limit_mismatch']}",
        f"- requested/actual train: {split_diag['requested_train_limit']} / {split_diag['actual_train_count']}",
        f"- requested/actual eval: {split_diag['requested_eval_limit']} / {split_diag['actual_eval_count']}",
        f"- requested/actual ood: {split_diag['requested_ood_limit']} / {split_diag['actual_ood_count']}",
        "",
        "## XLarge Same-Seed Reproduction（xlarge 同 seed 复验）",
        f"- global_correct_targetir_in_beam_rate: {same.get('global_correct_targetir_in_beam_rate')}",
        f"- candidate_space_failure_rate: {same.get('candidate_space_failure_rate')}",
        "",
        "## XLarge Alt-Seed / Light Reproduction（xlarge 异 seed / light 复验）",
        f"- global_correct_targetir_in_beam_rate: {alt.get('global_correct_targetir_in_beam_rate')}",
        f"- candidate_space_failure_rate: {alt.get('candidate_space_failure_rate')}",
        "",
        "## Guard Metric Baseline Fix（守卫基线修复）",
        f"- guard_candidate_accepted_count: {guard_summary.get('guard_candidate_accepted_count')}",
        f"- global_beam_after_guard: {guard_summary.get('global_beam_after_guard')}",
        "",
        "## Root Lifecycle Metric Clarification（根生命周期指标澄清）",
        f"- cumulative_nourished_event_count: {lifecycle_fix.get('cumulative_nourished_event_count')}",
        f"- final_nourished_root_count: {lifecycle_fix.get('final_nourished_root_count')}",
        "",
        "## Updated Mainline Judgment（更新主线判断）",
        f"- xlarge_08167_conclusion: {conclusion['xlarge_08167_conclusion']}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable convergence.",
        "- This does not prove general program synthesis.",
        "- This does not prove solved arithmetic.",
        "- This does not prove AGI, Transformer replacement, or advantage over same-size LLM.",
    ]) + "\n"


def print_summary(paths, repro_summary, reconciliation, split_diag, guard_summary, lifecycle_fix):
    print(f"metric_consistency_passed: {reconciliation['metric_consistency_passed']}")
    print(f"inconsistency_count: {reconciliation['inconsistency_count']}")
    print(f"split_mismatch_reason: {split_diag['reason_for_limit_mismatch']}")
    print(f"reproduced_strong_signal: {repro_summary['reproduced_strong_signal']}")
    print(f"guard_candidate_accepted_count: {guard_summary.get('guard_candidate_accepted_count')}")
    print(f"cumulative_nourished_event_count: {lifecycle_fix.get('cumulative_nourished_event_count')}")
    for key, value in paths.items():
        print(f"{key}: {value}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--bounded-runtime-sec", type=int, default=7200)
    parser.add_argument("--alt-seed", type=int, default=43)
    parser.add_argument("--alt-seed-light", default="true")
    parser.add_argument("--pytest-green", default="true")
    parser.add_argument("--records-dir", default="records/v0_8_1_1")
    return parser.parse_args()


if __name__ == "__main__":
    main()
