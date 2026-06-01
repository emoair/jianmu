from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ASSIGNMENTS = [
    ("loop_strengthening_assignment", "loop_bound_confusion", {"has_for_loop": True, "loop_bound_explicit": True, "branch_inside_loop": True, "update_order_explicit": True}, "current_supported", 4),
    ("condition_operator_assignment", "condition_operator_confusion", {"condition_operator_family": [">", ">=", "<", "<=", "==", "!="], "minimal_operator_contrast": True}, "current_supported", 4),
    ("update_order_assignment", "update_order_confusion", {"update_order_contrast": True, "pre_update_vs_post_update": True}, "current_supported", 5),
    ("output_variable_assignment", "output_variable_confusion", {"multi_variable_update": True, "output_variable_contrast": True}, "current_supported", 4),
    ("nested_control_assignment", "nested_control_confusion", {"has_nested_control": True, "nested_branch_loop": True}, "current_supported", 5),
    ("function_frontier_assignment", "function_frontier_gap", {"has_function": True, "bounded_call_graph": True}, "experimental_supported_function", 5),
    ("array_frontier_assignment", "array_frontier_gap", {"has_array": True, "safe_static_index": True}, "experimental_supported_array", 5),
    ("contrastive_code_module_assignment", "contrastive_structure_gap", {"minimal_operator_contrast": True, "output_variable_contrast": True, "update_order_contrast": True}, "current_supported", 5),
]


def build_redqueen_targeted_code_assignment(output_records: str | Path) -> Dict[str, Any]:
    profiles: List[Dict[str, Any]] = []
    for assignment_id, failure, required, support, difficulty in ASSIGNMENTS:
        profiles.append({
            "assignment_id": assignment_id,
            "target_failure": failure,
            "required_features": required,
            "forbidden_features": ["recursion", "pointer", "io", "system_call", "dynamic_allocation"],
            "difficulty_level": difficulty,
            "target_sample_count": 12000,
            "expected_gain_target": {"candidate_miss_delta": -0.002, "top1_delta": 0.002},
            "support_status_target": support,
            "safety_contract": {
                "boundary_defined_by_data_contract": True,
                "no_runtime_gate": True,
                "unsupported_features_isolated": True,
            },
        })
    result = {
        "redqueen_targeted_assignment_completed": True,
        "assignment_profiles": profiles,
        "redqueen_only_adjusts_required_features_and_curriculum": True,
    }
    out = Path(output_records)
    _write_json(out / "redqueen_targeted_code_assignment.json", result)
    (out / "redqueen_targeted_code_assignment.md").write_text("# RedQueen Targeted Code Assignment\n\n" + "\n".join(f"- {p['assignment_id']}: {p['target_failure']}" for p in profiles) + "\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
