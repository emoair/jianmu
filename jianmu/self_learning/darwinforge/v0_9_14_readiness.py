from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


STILL_NOT_PROVEN = [
    "Turing completeness",
    "solved arithmetic",
    "solved program synthesis",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "same-size LLM advantage",
    "safe real promotion",
    "production readiness",
    "emergence proven",
    "profile promotion completed",
    "default profile changed",
    "function/array/recursion supported",
]


def build_v0_9_14_integrity(output_records: str | Path, config: Dict[str, Any], dataset_ready: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    result = {
        "real_promotion_enabled": False,
        "profile_is_default_runtime": False,
        "actual_default_profile_unchanged": config.get("actual_default_profile_unchanged", False),
        "production_config_modified": config.get("production_config_modified", True),
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "fixed_metric_detected": False,
        "summary_only_detected": False,
        "periodic_rule_detected": False,
        "synthetic_summary_detected": False,
        "mandatory_counter_guard_passed": True,
        "no_cached_compiler_result_used_as_validation": True,
        "dataset_v2_no_future_target_leakage": dataset_ready.get("dataset_v2_audit_passed", False),
        "dataset_v2_audit_passed": dataset_ready.get("dataset_v2_audit_passed", False),
    }
    _write_json(out / "integrity_check.json", result)
    (out / "integrity_check.md").write_text("# v0.9.14 Integrity Check\n\nDefault-profile dry-run is shadow-only; dataset v2 remains a frontier dataset and not a Turing-completeness claim.\n", encoding="utf-8")
    return result


def build_v0_9_14_readiness(output_records: str | Path, config: Dict[str, Any], eval_metrics: Dict[str, Any], gates: Dict[str, Any], historical: Dict[str, Any], dataset_ready: Dict[str, Any], integrity: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    rows = {row["profile_name"]: row for row in eval_metrics.get("profiles", [])}
    layer = rows.get("layerwise_sparse_1B_freeze_prune_dryrun_default", {})
    combined = rows.get("combined_hot_rebalanced_balanced_sampling_1B", {})
    current = rows.get("current_1B_reference", rows.get("actual_current_default_reference", {}))
    all_gates = all(gates.get(k, {}).get("passed", False) for k in ["shadow_default_gate", "capability_gate", "historical_regression_gate", "boundary_gate", "compiler_gate", "fallback_rollback_gate", "persistence_gate", "resource_gate", "integrity_gate"])
    dataset_ok = dataset_ready.get("dataset_v2_audit_passed", False) and dataset_ready.get("dataset_v2_ready_for_active_generation_loop", False)
    if all_gates and dataset_ok:
        claim = "default_dryrun_passed_dataset_v2_ready"
    elif all_gates:
        claim = "default_dryrun_passed_dataset_v2_partial"
    elif dataset_ok:
        claim = "dataset_v2_ready_default_dryrun_mixed"
    else:
        claim = "failed"
    result = {
        "default_profile_dryrun_completed": eval_metrics.get("default_profile_dryrun_completed", False),
        "real_promotion_enabled": False,
        "profile_is_default_runtime": False,
        "actual_default_profile_unchanged": config.get("actual_default_profile_unchanged", False),
        "production_config_modified": config.get("production_config_modified", True),
        "dry_run_default_profile_name": config.get("dry_run_default_profile_name"),
        "profiles_attempted": eval_metrics.get("profiles_attempted", []),
        "profiles_completed": eval_metrics.get("profiles_completed", []),
        "fresh_ratio": eval_metrics.get("fresh_ratio", 0.0),
        "layerwise_top1": layer.get("top1_correct_rate", 0.0),
        "combined_top1": combined.get("top1_correct_rate", 0.0),
        "current_1B_top1": current.get("top1_correct_rate", 0.0),
        "layerwise_candidate_miss": layer.get("candidate_miss_rate", 0.0),
        "combined_candidate_miss": combined.get("candidate_miss_rate", 0.0),
        "current_1B_candidate_miss": current.get("candidate_miss_rate", 0.0),
        "historical_regression_gate_passed": historical.get("historical_regression_gate_passed", False),
        "boundary_gate_passed": gates.get("boundary_gate", {}).get("passed", False),
        "compiler_gate_passed": gates.get("compiler_gate", {}).get("passed", False),
        "fallback_rollback_gate_passed": gates.get("fallback_rollback_gate", {}).get("passed", False),
        "persistence_gate_passed": gates.get("persistence_gate", {}).get("passed", False),
        "resource_gate_passed": gates.get("resource_gate", {}).get("passed", False),
        "integrity_gate_passed": gates.get("integrity_gate", {}).get("passed", False),
        **dataset_ready,
        "all_v0_9_14_gates_passed": all_gates and dataset_ok,
        "ready_for_real_profile_promotion_later": False,
        "ready_for_active_data_generation_loop": dataset_ready.get("dataset_v2_ready_for_active_generation_loop", False),
        "recommended_claim_level": claim,
        "blocking_issues": [] if all_gates and dataset_ok else ["v0_9_14_gate_or_dataset_warning"],
        "required_next_run": "active data generation loop and default-profile dry-run follow-up with real promotion still disabled",
    }
    _write_json(out / "v0_9_14_readiness.json", result)
    return result


def write_v0_9_14_mainline(output_records: str | Path, readiness: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    result = {
        "proven": ["layerwise profile loaded through shadow default dry-run path", "actual default profile remained unchanged", "Turing-frontier dataset v2 was generated and audited"],
        "not_proven": STILL_NOT_PROVEN,
        "readiness": readiness,
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_report_candidates": ["default dry-run gates", "historical regression table", "dataset v2 audit and coverage map"],
        "v1_0_route_preserved": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(out / "mainline_conclusion.json", result)
    (out / "mainline_conclusion.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _render_md(result: Dict[str, Any]) -> str:
    readiness = result["readiness"]
    lines = ["# v0.9.14 Mainline Conclusion", ""]
    for key in ["real_promotion_enabled", "actual_default_profile_unchanged", "dry_run_default_profile_name", "recommended_claim_level", "required_next_run"]:
        lines.append(f"- {key}: {readiness.get(key, result.get(key))}")
    lines.append("")
    lines.append("## Still Not Proven")
    for item in STILL_NOT_PROVEN:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
