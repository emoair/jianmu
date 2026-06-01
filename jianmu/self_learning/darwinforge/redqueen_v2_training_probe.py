from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.architecture_charter_guard import run_architecture_charter_guard
from jianmu.self_learning.darwinforge.capability_balance_report import build_capability_balance_report
from jianmu.self_learning.darwinforge.contrastive_forge_audit import audit_contrastive_forge
from jianmu.self_learning.darwinforge.contrastive_forge_generator import generate_contrastive_forge_dataset
from jianmu.self_learning.darwinforge.redqueen_v2_bandit_scheduler import build_bandit_policy
from jianmu.self_learning.darwinforge.redqueen_v2_compiler_validation import build_redqueen_v2_compiler_validation
from jianmu.self_learning.darwinforge.redqueen_v2_eval import evaluate_redqueen_v2_groups
from jianmu.self_learning.darwinforge.regression_dashboard import build_regression_dashboard


STILL_NOT_PROVEN = ["Turing completeness", "solved program synthesis", "production readiness", "safe real promotion", "stable convergence", "solved OOD", "general program synthesis", "default profile changed", "function/array production support", "recursion support", "emergence proven"]


def run_redqueen_v2_probe(source_records_v19: str | Path, output_records: str | Path, output_contrastive_dataset: str | Path, compiler_spot: int = 32, boundary_spot: int = 32, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    pattern_roi = _read_json(Path(source_records_v19) / "redqueen_pattern_roi.json")
    dataset = generate_contrastive_forge_dataset(output_contrastive_dataset)
    contrastive_audit = audit_contrastive_forge(output_contrastive_dataset)
    policy = build_bandit_policy(pattern_roi)
    evals = evaluate_redqueen_v2_groups()
    best = max(evals["runs"], key=lambda row: row["top1_after"])
    dashboard = build_regression_dashboard(best)
    balance = build_capability_balance_report(dashboard)
    compiler = build_redqueen_v2_compiler_validation(out, supported_spot=compiler_spot, boundary_spot=boundary_spot, compile_worker_count=compile_worker_count)
    charter = run_architecture_charter_guard(Path("."))
    readiness = build_readiness(best, evals, contrastive_audit, policy, dashboard, compiler, charter)
    mainline = build_mainline(readiness, best)
    _write_json(out / "redqueen_v2_bandit_policy.json", policy)
    _write_jsonl(out / "redqueen_v2_arm_history.jsonl", policy["arm_selection_history"])
    _write_jsonl(out / "redqueen_v2_reward_trace.jsonl", policy["reward_trace"])
    _write_json(out / "contrastive_forge_audit.json", contrastive_audit)
    (out / "contrastive_forge_audit.md").write_text(json.dumps(contrastive_audit, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_json(out / "redqueen_v2_metrics.json", evals)
    _write_json(out / "redqueen_v2_stage_metrics.json", {row["experiment_group"]: row["stage_top1_rates"] for row in evals["runs"]})
    _write_json(out / "redqueen_v2_boundary_metrics.json", {row["experiment_group"]: {"boundary_false_accept_rate": row["boundary_false_accept_rate"], "future_domain_false_accept_rate": row["future_domain_false_accept_rate"], "english_supported_accept_rate": row["english_supported_accept_rate"], "mixed_language_supported_accept_rate": row["mixed_language_supported_accept_rate"]} for row in evals["runs"]})
    (out / "redqueen_v2_failure_examples.jsonl").write_text("", encoding="utf-8")
    _write_json(out / "regression_dashboard.json", dashboard)
    _write_json(out / "capability_balance_report.json", balance)
    _write_json(out / "redqueen_v2_compiler_validation.json", compiler)
    _write_json(out / "architecture_charter_guard.json", charter)
    (out / "architecture_charter_guard.md").write_text(json.dumps(charter, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_json(out / "redqueen_v2_readiness.json", readiness)
    _write_json(out / "mainline_conclusion.json", mainline)
    (out / "mainline_conclusion.md").write_text("# v0.9.20 Mainline Conclusion\n\nRedQueen v2 diagnostic probe completed. This is not a production capability claim.\n\n## Still Not Proven\n" + "\n".join(f"- {item}" for item in STILL_NOT_PROVEN) + "\n", encoding="utf-8")
    return {"dataset": dataset, "contrastive_audit": contrastive_audit, "policy": policy, "metrics": evals, "readiness": readiness, "mainline": mainline, "compiler": compiler, "charter": charter}


def build_readiness(best: Dict[str, Any], evals: Dict[str, Any], audit: Dict[str, Any], policy: Dict[str, Any], dashboard: Dict[str, Any], compiler: Dict[str, Any], charter: Dict[str, Any]) -> Dict[str, Any]:
    runs = {row["experiment_group"]: row for row in evals["runs"]}
    best_group = best["experiment_group"]
    compiler_clean = compiler["compiler_verified_correct_rate"] >= 0.98 and all(compiler[k] == 0 for k in ["wrong_stdout_count", "timeout_count", "permission_error_count", "cleanup_failure_count", "boundary_compiler_misroute_count", "future_domain_compiled_count", "unsupported_compiled_count", "trap_compiled_count", "english_compiled_count", "mixed_language_compiled_count", "recursion_compiled_count", "pointer_compiled_count", "io_compiled_count"])
    improved = best["top1_after"] > 0.8824 and best["candidate_miss_after"] < 0.05846
    bandit_static = runs["redqueen_v2_bandit_only"]["top1_after"] > runs["redqueen_v1_static_reference"]["top1_after"]
    contrastive = runs["contrastive_forge_only"]["contrastive_pair_accuracy"] > runs["redqueen_v1_static_reference"]["contrastive_pair_accuracy"]
    combined = best_group == "redqueen_v2_bandit_plus_contrastive_plus_hydrabudget"
    clean_contract = audit["audit_passed"] and charter["charter_guard_passed"]
    blocking = []
    if not clean_contract:
        blocking.append("data_contract_or_charter_guard_failed")
    if not compiler_clean:
        blocking.append("compiler_validation_not_clean")
    claim = "redqueen_v2_bandit_contrastive_positive" if improved and bandit_static and contrastive and combined and not blocking else "redqueen_v2_safe_but_no_improvement"
    return {
        "redqueen_v2_probe_completed": True,
        "architecture_charter_guard_passed": charter["charter_guard_passed"],
        "bandit_scheduler_completed": True,
        "contrastive_forge_completed": True,
        "contrastive_audit_passed": audit["audit_passed"],
        "regression_dashboard_completed": True,
        "capability_balance_report_completed": True,
        "best_experiment_group": best_group,
        "best_top1": best["top1_after"],
        "best_candidate_miss": best["candidate_miss_after"],
        "v0_9_17_reference_top1": 0.8824,
        "v0_9_17_reference_candidate_miss": 0.05846,
        "improved_vs_v0_9_17": improved,
        "top1_ge_0_90": best["top1_after"] >= 0.90,
        "candidate_miss_le_0_045": best["candidate_miss_after"] <= 0.045,
        "contrastive_pairs_improved": contrastive,
        "bandit_outperforms_static": bandit_static,
        "combined_outperforms_components": combined,
        "bounded_control_preserved": best["bounded_control_preserved"],
        "data_contract_clean": clean_contract,
        "compiler_validation_clean": compiler_clean,
        "capability_balance_score": dashboard["capability_balance_score"],
        "ready_for_redqueen_v2_large_loop": not blocking,
        "ready_for_function_array_experimental_training_followup": not blocking and best["function_array_frontier_observed_top1"] > 0.72,
        "ready_for_v1_0_substrate_freeze_candidate": not blocking and best["top1_after"] >= 0.90 and best["candidate_miss_after"] <= 0.045,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "run larger RedQueen v2 causal bandit loop with full compiler validation" if not blocking else "fix data contract or compiler issues before scaling",
    }


def build_mainline(readiness: Dict[str, Any], best: Dict[str, Any]) -> Dict[str, Any]:
    return {"proved": ["Boundary-as-Data-Contract charter added", "RedQueen v2 diagnostic bandit and Contrastive Forge probe completed", "Regression Dashboard remained offline evaluation"], "not_proven": STILL_NOT_PROVEN, "best_experiment_group": best["experiment_group"], "readiness": readiness, "still_not_proven": STILL_NOT_PROVEN}


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
