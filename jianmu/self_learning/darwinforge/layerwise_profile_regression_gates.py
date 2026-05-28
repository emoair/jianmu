from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_layerwise_profile_regression_gates(
    output_records: str | Path,
    shadow_metrics: Dict[str, Any],
    compiler_metrics: Dict[str, Any],
    persistence: Dict[str, Any],
    resource_audit: Dict[str, Any],
    integrity: Dict[str, Any],
) -> Dict[str, Any]:
    out = Path(output_records)
    rows = {row["profile_name"]: row for row in shadow_metrics.get("profiles", [])}
    current = rows.get("current_1B_reference", {})
    combined = rows.get("combined_hot_rebalanced_balanced_sampling_1B", {})
    layerwise = rows.get("layerwise_sparse_1B_freeze_prune", {})
    stage_bad = _stage_bad_regression(layerwise, combined)
    gates = {
        "capability_gate": _gate(
            layerwise.get("top1_correct_rate", 0.0) > current.get("top1_correct_rate", 0.0)
            and layerwise.get("top1_correct_rate", 0.0) >= combined.get("top1_correct_rate", 0.0)
            and layerwise.get("candidate_miss_rate", 1.0) < current.get("candidate_miss_rate", 1.0)
            and layerwise.get("candidate_miss_rate", 1.0) <= combined.get("candidate_miss_rate", 1.0),
            {"current_top1": current.get("top1_correct_rate"), "combined_top1": combined.get("top1_correct_rate"), "layerwise_top1": layerwise.get("top1_correct_rate"), "current_candidate_miss": current.get("candidate_miss_rate"), "combined_candidate_miss": combined.get("candidate_miss_rate"), "layerwise_candidate_miss": layerwise.get("candidate_miss_rate")},
        ),
        "stage_gate": _gate(not stage_bad, {"bad_regression_stages": stage_bad}, "blocking" if stage_bad else "informational"),
        "boundary_gate": _gate(
            layerwise.get("future_domain_supported_accept_rate", 1.0) == 0
            and layerwise.get("boundary_false_accept_rate", 1.0) == 0
            and layerwise.get("trap_false_accept_rate", 1.0) == 0
            and layerwise.get("near_ood_supported_accept_rate", 1.0) <= 0.05,
            {"future_domain_supported_accept_rate": layerwise.get("future_domain_supported_accept_rate"), "boundary_false_accept_rate": layerwise.get("boundary_false_accept_rate"), "near_ood_supported_accept_rate": layerwise.get("near_ood_supported_accept_rate"), "trap_false_accept_rate": layerwise.get("trap_false_accept_rate")},
        ),
        "compiler_gate": _gate(
            compiler_metrics.get("compiler_verified_correct_rate", 0.0) >= 0.98
            and compiler_metrics.get("permission_error_count", 0) == 0
            and compiler_metrics.get("cleanup_failure_count", 0) == 0
            and compiler_metrics.get("wrong_stdout_count", 0) == 0
            and compiler_metrics.get("boundary_compiler_misroute_count", 0) == 0
            and compiler_metrics.get("future_domain_compiled_count", 0) == 0,
            {key: compiler_metrics.get(key) for key in ["compiler_verified_correct_rate", "permission_error_count", "cleanup_failure_count", "wrong_stdout_count", "boundary_compiler_misroute_count", "future_domain_compiled_count"]},
        ),
        "persistence_gate": _gate(
            persistence.get("cross_process_reload_passed", False)
            and persistence.get("child_forbidden_field_access_count", 1) == 0
            and persistence.get("child_metrics_comparable", False),
            persistence,
        ),
        "resource_gate": _gate(
            resource_audit.get("layerwise_resource_overhead_acceptable", False)
            and resource_audit.get("layerwise_profile_cost_effective", False),
            {"layerwise_resource_overhead_acceptable": resource_audit.get("layerwise_resource_overhead_acceptable"), "layerwise_overhead_vs_combined": resource_audit.get("layerwise_overhead_vs_combined"), "layerwise_profile_cost_effective": resource_audit.get("layerwise_profile_cost_effective")},
            "warning" if not resource_audit.get("layerwise_resource_overhead_acceptable", False) else "informational",
        ),
        "integrity_gate": _gate(
            integrity.get("forbidden_field_access_count", 1) == 0
            and not integrity.get("fixed_metric_detected", True)
            and not integrity.get("summary_only_detected", True)
            and not integrity.get("periodic_rule_detected", True)
            and integrity.get("no_cached_compiler_result_used_as_validation", False)
            and not integrity.get("real_promotion_enabled", True),
            integrity,
        ),
    }
    result = {
        "regression_gates_completed": True,
        **gates,
        "capability_gate_passed": gates["capability_gate"]["passed"],
        "stage_gate_passed": gates["stage_gate"]["passed"],
        "boundary_gate_passed": gates["boundary_gate"]["passed"],
        "compiler_gate_passed": gates["compiler_gate"]["passed"],
        "persistence_gate_passed": gates["persistence_gate"]["passed"],
        "resource_gate_passed": gates["resource_gate"]["passed"],
        "integrity_gate_passed": gates["integrity_gate"]["passed"],
        "all_promotion_probe_gates_passed": all(gate["passed"] for gate in gates.values()),
    }
    _write_json(out / "regression_gates.json", result)
    (out / "regression_gates.md").write_text("# v0.9.13 Regression Gates\n\nAll gates are shadow promotion-probe gates only. Real promotion remains disabled.\n", encoding="utf-8")
    return result


def _stage_bad_regression(layerwise: Dict[str, Any], combined: Dict[str, Any]) -> list[str]:
    bad = []
    layer_stages = layerwise.get("stage_top1_rates", {})
    combined_stages = combined.get("stage_top1_rates", {})
    for stage in ["if_else_basic", "if_else_nested", "bounded_for_loop", "bounded_while_with_fuel", "nested_bounded_control", "bounded_control_hard_supported"]:
        if layer_stages.get(stage, 0.0) - combined_stages.get(stage, 0.0) < -0.03:
            bad.append(stage)
    return bad


def _gate(passed: bool, metric_values: Dict[str, Any], severity: str = "informational") -> Dict[str, Any]:
    return {"passed": bool(passed), "metric_values": metric_values, "failure_reason": "" if passed else "gate condition not met", "severity": severity if not passed else "informational"}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
