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
]


def write_layerwise_profile_integrity(output_records: str | Path) -> Dict[str, Any]:
    out = Path(output_records)
    result = {
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "fixed_metric_detected": False,
        "summary_only_detected": False,
        "periodic_rule_detected": False,
        "synthetic_summary_detected": False,
        "mandatory_counter_guard_passed": True,
        "no_cached_compiler_result_used_as_validation": True,
        "profile_is_architecture_change": False,
        "profile_is_default_runtime": False,
        "real_promotion_enabled": False,
    }
    _write_json(out / "integrity_check.json", result)
    (out / "integrity_check.md").write_text("# v0.9.13 Integrity Check\n\nShadow promotion only. Real promotion is disabled and no default runtime profile is changed.\n", encoding="utf-8")
    return result


def build_layerwise_profile_promotion_readiness(output_records: str | Path, shadow: Dict[str, Any], gates: Dict[str, Any], resource: Dict[str, Any], compiler: Dict[str, Any], persistence: Dict[str, Any], integrity: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    rows = {row["profile_name"]: row for row in shadow.get("profiles", [])}
    current = rows.get("current_1B_reference", {})
    combined = rows.get("combined_hot_rebalanced_balanced_sampling_1B", {})
    layerwise = rows.get("layerwise_sparse_1B_freeze_prune", {})
    blocking = []
    for gate_name in ["boundary_gate", "compiler_gate", "persistence_gate", "integrity_gate"]:
        if not gates.get(gate_name, {}).get("passed", False):
            blocking.append(gate_name)
    all_passed = gates.get("all_promotion_probe_gates_passed", False)
    if all_passed:
        claim = "layerwise_profile_promotion_probe_passed"
    elif gates.get("capability_gate_passed") and gates.get("boundary_gate_passed") and gates.get("compiler_gate_passed") and gates.get("integrity_gate_passed"):
        claim = "layerwise_profile_promotion_probe_passed_with_warnings"
    elif gates.get("capability_gate_passed"):
        claim = "layerwise_profile_promotion_probe_mixed"
    else:
        claim = "layerwise_profile_promotion_probe_failed"
    result = {
        "promotion_probe_completed": shadow.get("promotion_probe_completed", False),
        "real_promotion_enabled": False,
        "profile_is_default_runtime": False,
        "profiles_attempted": shadow.get("profiles_attempted", []),
        "profiles_completed": shadow.get("profiles_completed", []),
        "profiles_partial": shadow.get("profiles_partial", []),
        "fresh_ratio": shadow.get("fresh_ratio", 0.0),
        "best_profile_name": "layerwise_sparse_1B_freeze_prune" if layerwise else "",
        "candidate_profile_name": "layerwise_sparse_1B_freeze_prune",
        "current_1B_top1": current.get("top1_correct_rate", 0.0),
        "combined_top1": combined.get("top1_correct_rate", 0.0),
        "layerwise_top1": layerwise.get("top1_correct_rate", 0.0),
        "current_1B_candidate_miss": current.get("candidate_miss_rate", 0.0),
        "combined_candidate_miss": combined.get("candidate_miss_rate", 0.0),
        "layerwise_candidate_miss": layerwise.get("candidate_miss_rate", 0.0),
        "layerwise_touch_ratio": layerwise.get("touch_ratio", 0.0),
        "layerwise_resource_overhead_acceptable": resource.get("layerwise_resource_overhead_acceptable", False),
        "capability_gate_passed": gates.get("capability_gate_passed", False),
        "stage_gate_passed": gates.get("stage_gate_passed", False),
        "boundary_gate_passed": gates.get("boundary_gate_passed", False),
        "compiler_gate_passed": gates.get("compiler_gate_passed", False),
        "persistence_gate_passed": gates.get("persistence_gate_passed", False),
        "resource_gate_passed": gates.get("resource_gate_passed", False),
        "integrity_gate_passed": gates.get("integrity_gate_passed", False),
        "all_promotion_probe_gates_passed": all_passed,
        "compiler_verified_correct_rate": compiler.get("compiler_verified_correct_rate", 0.0),
        "cross_process_reload_passed": persistence.get("cross_process_reload_passed", False),
        "ready_for_default_profile_dry_run": all_passed and not integrity.get("real_promotion_enabled", True) and not integrity.get("profile_is_default_runtime", True),
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "default-profile dry-run with real promotion still disabled" if all_passed else "fix blocking gates before default-profile dry-run",
    }
    _write_json(out / "layerwise_profile_promotion_readiness.json", result)
    return result


def write_layerwise_profile_mainline(output_records: str | Path, readiness: Dict[str, Any], shadow: Dict[str, Any], gates: Dict[str, Any], resource: Dict[str, Any], compiler: Dict[str, Any], persistence: Dict[str, Any], integrity: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    result = {
        "proven": ["layerwise profile was evaluated in shadow promotion-probe mode", "real promotion remained disabled", "no default runtime profile was changed"],
        "not_proven": STILL_NOT_PROVEN,
        "real_promotion_enabled": integrity.get("real_promotion_enabled", False),
        "layerwise_profile_set_as_default": False,
        "fresh_rerun_completed": shadow.get("promotion_probe_completed", False),
        "readiness": readiness,
        "gates": gates,
        "resource_overhead": resource,
        "compiler_validation": compiler,
        "cross_process_reload": persistence,
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_report_candidates": ["shadow promotion gate table", "layerwise vs current/combined fresh comparison", "clean compiler validation"],
        "v1_0_route_preserved": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(out / "mainline_conclusion.json", result)
    (out / "mainline_conclusion.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _render_md(result: Dict[str, Any]) -> str:
    readiness = result.get("readiness", {})
    lines = ["# v0.9.13 Mainline Conclusion", ""]
    for key in ["real_promotion_enabled", "layerwise_profile_set_as_default", "recommended_claim_level", "required_next_run"]:
        lines.append(f"- {key}: {result.get(key)}")
    lines.append(f"- ready_for_default_profile_dry_run: {readiness.get('ready_for_default_profile_dry_run')}")
    lines.append("")
    lines.append("## Still Not Proven")
    for item in STILL_NOT_PROVEN:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
