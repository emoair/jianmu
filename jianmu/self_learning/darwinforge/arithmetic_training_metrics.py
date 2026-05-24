from __future__ import annotations

from typing import Any, Dict, List


def build_arithmetic_training_metrics(summary: Dict[str, Any]) -> Dict[str, Any]:
    return dict(summary)


def stage_metric_row(stage_name: str, train_count: int, eval_count: int, before: Dict[str, Any], after: Dict[str, Any], branch_updates: int, root_updates: int, runtime_seconds: float) -> Dict[str, Any]:
    return {
        "stage_name": stage_name,
        "train_sample_count": train_count,
        "eval_sample_count": eval_count,
        "supported_success_before": before.get("supported_correct_output_in_beam_rate", 0.0),
        "supported_success_after": after.get("supported_correct_output_in_beam_rate", 0.0),
        "candidate_hit_before": before.get("supported_candidate_in_beam_rate", 0.0),
        "candidate_hit_after": after.get("supported_candidate_in_beam_rate", 0.0),
        "ood_false_accept_before": before.get("false_accept_rate", 0.0),
        "ood_false_accept_after": after.get("false_accept_rate", 0.0),
        "false_reject_before": before.get("false_reject_rate", 0.0),
        "false_reject_after": after.get("false_reject_rate", 0.0),
        "nutrient_reward_total": float(train_count),
        "toxicity_total": 0.0,
        "root_updates": root_updates,
        "branch_updates": branch_updates,
        "stage_runtime_seconds": round(runtime_seconds, 6),
        "stage_passed": after.get("forbidden_field_access_count", 1) == 0,
    }
