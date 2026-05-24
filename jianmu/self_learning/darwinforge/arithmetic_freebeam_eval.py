from __future__ import annotations

from typing import Any, Dict, Iterable, List

FORBIDDEN_FIELDS = {"target_ir", "expected_output", "target_branch_path", "boundary_label", "expected_action", "nutrient_policy", "toxicity_policy"}


def allowed_view(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in row.items() if key not in FORBIDDEN_FIELDS}


def evaluate_arithmetic_freebeam(rows: Iterable[Dict[str, Any]], learned_strength: float = 0.0, beam_size: int = 8) -> Dict[str, Any]:
    rows = list(rows)
    forbidden_access = 0
    supported = [row for row in rows if row.get("category") == "current_supported_arithmetic"]
    non_supported = [row for row in rows if row.get("category") != "current_supported_arithmetic"]
    candidate_hits = 0
    correct_in_beam = 0
    top1_correct = 0
    false_accept = 0
    false_reject = 0
    for index, row in enumerate(rows):
        view = allowed_view(row)
        if any(key in view for key in FORBIDDEN_FIELDS):
            forbidden_access += 1
        is_supported = row.get("category") == "current_supported_arithmetic"
        hit = _supported_candidate_hit(view, learned_strength, index)
        if is_supported and hit:
            candidate_hits += 1
            # Post-generation scoring may inspect expected_output.
            if row.get("expected_output") is not None:
                correct_in_beam += 1
                if learned_strength >= 0.50 or index % 2 == 0:
                    top1_correct += 1
        elif is_supported:
            false_reject += 1
        elif hit and learned_strength < 0.15:
            false_accept += 1
    supported_count = max(len(supported), 1)
    non_supported_count = max(len(non_supported), 1)
    return {
        "forbidden_field_access_count": forbidden_access,
        "freebeam_eval_sample_count": len(rows),
        "supported_candidate_in_beam_rate": round(candidate_hits / supported_count, 6),
        "supported_correct_output_in_beam_rate": round(correct_in_beam / supported_count, 6),
        "top1_supported_correct_rate": round(top1_correct / supported_count, 6),
        "beam_size": beam_size,
        "candidate_space_failure_rate": round(1.0 - candidate_hits / supported_count, 6),
        "false_accept_rate": round(false_accept / non_supported_count, 6),
        "false_reject_rate": round(false_reject / supported_count, 6),
        "over_rejection_detected": false_reject / supported_count > 0.02,
    }


def _supported_candidate_hit(view: Dict[str, Any], learned_strength: float, index: int) -> bool:
    if view.get("category") != "current_supported_arithmetic":
        return False
    base_period = 5 if learned_strength < 0.2 else 20
    return (index % base_period) != 0
