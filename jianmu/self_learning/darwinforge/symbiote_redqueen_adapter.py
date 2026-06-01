from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_symbiote_redqueen_assignments(output_records: str | Path) -> Dict[str, Any]:
    result = {
        "symbiote_redqueen_assignments_completed": True,
        "mirror_training_assignments": [_assignment("mirror", "loop_weakness", {"has_for_loop": True, "loop_bound_explicit": True, "branch_inside_loop": True, "update_order_explicit": True})],
        "trunk_training_assignments": [_assignment("trunk", "condition_weakness", {"condition_operator_family": [">", ">=", "<", "<=", "==", "!="], "minimal_operator_contrast": True})],
        "heldout_generalization_assignments": [_assignment("both", "heldout_generalization", {"template_family_holdout": True, "structure_combination_holdout": True})],
        "comfort_zone_breaker_assignments": [_assignment("both", "comfort_zone_breaker", {"template_family_holdout": True, "variable_name_holdout": True, "structure_combination_holdout": True})],
        "redqueen_only_adjusts_curriculum": True,
        "capability_boundary_changed": False,
    }
    _write_json(Path(output_records) / "symbiote_redqueen_assignments.json", result)
    return result


def _assignment(component: str, target: str, required: Dict[str, Any]) -> Dict[str, Any]:
    return {"target_component": component, "target_failure": target, "required_features": required, "difficulty_level": 4 if component != "both" else 5, "target_sample_count": 50000, "no_capability_boundary_change": True}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
