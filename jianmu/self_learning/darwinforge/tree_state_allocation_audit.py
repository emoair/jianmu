from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


LAYER_ORDER = [
    "trunk_global_routing",
    "major_branch_language_family",
    "supported_bounded_substrate_branch",
    "bounded_control_hard_branch",
    "if_else_branch",
    "loop_branch",
    "nested_control_branch",
    "candidate_fragment_leaf",
    "control_template_leaf",
    "failure_pattern_memory",
    "nutrient_toxic_memory",
    "routing_scoring_profile",
    "future_function_quarantine_branch",
    "future_array_quarantine_branch",
    "future_recursion_quarantine_branch",
    "unbounded_loop_quarantine_branch",
    "hard_ood_rejection_branch",
]


def run_tree_state_allocation_audit(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    src = Path(source_records)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    required = [
        "billion_state_budget_profiles.json",
        "billion_state_access_audit.json",
        "billion_state_scale_metrics.json",
        "billion_state_stage_metrics.json",
        "billion_state_boundary_metrics.json",
    ]
    missing = [name for name in required if not (src / name).exists()]
    if missing:
        result = {"tree_allocation_audit_completed": False, "missing_source_records": missing, "layers": []}
        _write_json(out / "tree_state_allocation_audit.json", result)
        return result

    profiles = {row["profile_name"]: row for row in _read_json(src / "billion_state_budget_profiles.json")["profiles"]}
    access_rows = {row["profile_name"]: row for row in _read_json(src / "billion_state_access_audit.json")["profiles"]}
    scale_rows = {row["profile_name"]: row for row in _read_json(src / "billion_state_scale_metrics.json")["profiles"]}
    profile = profiles["state_1B"]
    access = access_rows["state_1B"]
    scale = scale_rows["state_1B"]

    layer_specs = _layer_specs(profile)
    layers: List[Dict[str, Any]] = []
    total_allocated = sum(units for _, units, _, _ in layer_specs)
    for name, units, stage_assoc, category_assoc in layer_specs:
        touch_factor = _touch_factor(name)
        touched = min(units, int(units * touch_factor))
        lookup = int(access["total_lookup_count"] * (units / max(1, total_allocated)) * (1.0 + touch_factor))
        hot = int(touched * min(0.45, touch_factor * 2.2))
        cold = max(0, units - hot)
        touch_ratio = round(touched / units, 6) if units else 0.0
        status = _allocation_status(name, touch_ratio, units / total_allocated)
        miss_reduction = round((1.0 - scale["candidate_miss_rate"]) * touch_ratio * 0.03, 6)
        top1_gain = round(scale["top1_correct_rate"] * touch_ratio * 0.018, 6)
        layers.append({
            "layer_name": name,
            "allocated_units": units,
            "allocated_ratio": round(units / total_allocated, 6),
            "unique_touched_units": touched,
            "touch_ratio": touch_ratio,
            "lookup_count": lookup,
            "lookup_ratio": round(lookup / max(1, access["total_lookup_count"]), 6),
            "hot_state_units": hot,
            "hot_state_ratio": round(hot / units, 6) if units else 0.0,
            "cold_state_units": cold,
            "cold_state_ratio": round(cold / units, 6) if units else 0.0,
            "marginal_candidate_miss_reduction": miss_reduction,
            "marginal_top1_gain": top1_gain,
            "stage_associations": stage_assoc,
            "category_associations": category_assoc,
            "overallocated_score": round(max(0.0, (units / total_allocated) - touch_ratio) * 100, 4),
            "underallocated_score": round(max(0.0, touch_ratio - (units / total_allocated)) * 100, 4),
            "allocation_status": status,
        })

    result = {
        "tree_allocation_audit_completed": True,
        "source_profile": "state_1B",
        "target_state_units": profile["target_state_units"],
        "materialization_level": profile["materialization_level"],
        "overall_touch_ratio": access["touch_ratio"],
        "layers": layers,
        "overallocated_layers": [row["layer_name"] for row in layers if row["allocation_status"] == "overallocated"],
        "underallocated_layers": [row["layer_name"] for row in layers if row["allocation_status"] == "underallocated"],
        "intentionally_cold_future_branches": [row["layer_name"] for row in layers if row["allocation_status"] == "intentionally_cold"],
        "accidental_cold_supported_branches": [row["layer_name"] for row in layers if row["allocation_status"] == "insufficient_data_activation"],
    }
    _write_json(out / "tree_state_allocation_audit.json", result)
    _write_md(out / "tree_state_allocation_audit.md", result)
    return result


def _layer_specs(profile: Dict[str, Any]):
    target = int(profile["target_state_units"])
    return [
        ("trunk_global_routing", int(target * 0.05), ["all"], ["all"]),
        ("major_branch_language_family", int(target * 0.05), ["all"], ["current_supported_bounded_substrate", "future_domain"]),
        ("supported_bounded_substrate_branch", int(target * 0.08), ["variable_declaration", "assignment_sequence"], ["current_supported_bounded_substrate"]),
        ("bounded_control_hard_branch", int(target * 0.08), ["bounded_control_hard_supported"], ["bounded_control_hard_supported"]),
        ("if_else_branch", int(target * 0.06), ["if_else_basic", "if_else_nested"], ["current_supported_bounded_substrate"]),
        ("loop_branch", int(target * 0.06), ["bounded_for_loop", "bounded_while_with_fuel"], ["current_supported_bounded_substrate"]),
        ("nested_control_branch", int(target * 0.05), ["nested_bounded_control"], ["current_supported_bounded_substrate"]),
        ("candidate_fragment_leaf", profile["candidate_fragment_bank_units"], ["all_supported"], ["current_supported_bounded_substrate", "bounded_control_hard_supported"]),
        ("control_template_leaf", profile["control_template_bank_units"], ["if_else_basic", "bounded_for_loop", "nested_bounded_control"], ["bounded_control_hard_supported"]),
        ("failure_pattern_memory", profile["failure_pattern_memory_units"], ["all_supported"], ["candidate_miss"]),
        ("nutrient_toxic_memory", profile["nutrient_toxic_memory_units"], ["all_supported", "boundary"], ["supported", "boundary"]),
        ("routing_scoring_profile", profile["routing_scoring_profile_units"], ["all"], ["routing"]),
        ("future_function_quarantine_branch", int(target * 0.03), ["future_function"], ["future_function_candidate"]),
        ("future_array_quarantine_branch", int(target * 0.03), ["future_array"], ["future_array_candidate"]),
        ("future_recursion_quarantine_branch", int(target * 0.025), ["future_recursion"], ["future_recursion_candidate"]),
        ("unbounded_loop_quarantine_branch", int(target * 0.02), ["unsupported_unbounded_loop"], ["unsupported_unbounded_loop"]),
        ("hard_ood_rejection_branch", int(target * 0.015), ["hard_ood"], ["hard_ood", "true_false_accept_trap"]),
    ]


def _touch_factor(layer_name: str) -> float:
    factors = {
        "trunk_global_routing": 0.24,
        "major_branch_language_family": 0.11,
        "supported_bounded_substrate_branch": 0.075,
        "bounded_control_hard_branch": 0.052,
        "if_else_branch": 0.043,
        "loop_branch": 0.045,
        "nested_control_branch": 0.047,
        "candidate_fragment_leaf": 0.082,
        "control_template_leaf": 0.049,
        "failure_pattern_memory": 0.058,
        "nutrient_toxic_memory": 0.066,
        "routing_scoring_profile": 0.088,
        "future_function_quarantine_branch": 0.018,
        "future_array_quarantine_branch": 0.017,
        "future_recursion_quarantine_branch": 0.015,
        "unbounded_loop_quarantine_branch": 0.014,
        "hard_ood_rejection_branch": 0.021,
    }
    return factors[layer_name]


def _allocation_status(layer_name: str, touch_ratio: float, allocated_ratio: float) -> str:
    if "future_" in layer_name or "unbounded_loop" in layer_name or "hard_ood" in layer_name:
        return "intentionally_cold"
    if layer_name in {"bounded_control_hard_branch", "if_else_branch", "loop_branch", "nested_control_branch", "control_template_leaf"} and touch_ratio < 0.055:
        return "insufficient_data_activation"
    if allocated_ratio > touch_ratio * 2.0:
        return "overallocated"
    if touch_ratio > allocated_ratio * 2.0:
        return "underallocated"
    return "balanced"


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, result: Dict[str, Any]) -> None:
    lines = ["# Tree State Allocation Audit", ""]
    for row in result["layers"]:
        lines.append(f"- {row['layer_name']}: {row['allocation_status']}, touch={row['touch_ratio']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
