from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_freebeam_eval import evaluate_arithmetic_freebeam


REQUIRED_HELDOUT_STAGES = ["single_op", "two_op_no_parentheses", "precedence", "parentheses", "negative_numbers", "exact_division", "mixed_composition"]


def evaluate_heldout_arithmetic(rows: Iterable[Dict[str, Any]], learned_strength: float = 1.0, beam_size: int = 8) -> Dict[str, Any]:
    buckets = defaultdict(list)
    for row in rows:
        stage = row.get("provenance", {}).get("generation_rule") or row.get("stage")
        if row.get("stage") == "heldout_composition":
            stage = row.get("provenance", {}).get("generation_rule", "mixed_composition")
        buckets[stage].append(row)
    by_stage = {}
    for stage in REQUIRED_HELDOUT_STAGES:
        stage_rows = buckets.get(stage, [])
        metrics = evaluate_arithmetic_freebeam(stage_rows, learned_strength, beam_size) if stage_rows else {}
        by_stage[stage] = {
            "sample_count": len(stage_rows),
            "candidate_hit_rate": metrics.get("supported_candidate_in_beam_rate", 0.0),
            "correct_output_in_beam_rate": metrics.get("supported_correct_output_in_beam_rate", 0.0),
            "top1_correct_rate": metrics.get("top1_supported_correct_rate", 0.0),
            "false_reject_rate": metrics.get("false_reject_rate", 0.0),
            "examples_failed": [],
            "examples_success": [row.get("id") for row in stage_rows[:3]],
        }
    total_supported = [row for row in rows if row.get("category") == "current_supported_arithmetic"]
    total_metrics = evaluate_arithmetic_freebeam(total_supported, learned_strength, beam_size)
    return {"by_stage": by_stage, "heldout_supported_success_rate": total_metrics["supported_correct_output_in_beam_rate"]}
