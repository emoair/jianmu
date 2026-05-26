from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


REQUIRED_HELDOUT_STAGES = [
    "variable_declaration",
    "assignment_sequence",
    "multi_variable_sequence",
    "if_else_basic",
    "if_else_nested",
    "bounded_for_loop",
    "bounded_while_with_fuel",
    "nested_bounded_control",
]


def summarize_heldout(trace: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in trace:
        if row.get("category") == "current_supported_turing_substrate":
            buckets[row.get("stage")].append(row)
    by_stage = {}
    for stage in REQUIRED_HELDOUT_STAGES:
        rows = buckets.get(stage, [])
        by_stage[stage] = {
            "sample_count": len(rows),
            "candidate_hit_rate": _rate(sum(1 for r in rows if r.get("candidate_hit")), len(rows)),
            "correct_output_in_beam_rate": _rate(sum(1 for r in rows if r.get("correct_output_in_beam")), len(rows)),
            "top1_correct_rate": _rate(sum(1 for r in rows if r.get("top1_correct")), len(rows)),
            "compiler_verified_correct_rate": _rate(sum(1 for r in rows if r.get("top1_correct")), len(rows)),
            "false_reject_rate": _rate(sum(1 for r in rows if not r.get("candidate_hit")), len(rows)),
            "examples_failed": [r["sample_id_hash"] for r in rows if not r.get("top1_correct")][:10],
            "examples_success": [r["sample_id_hash"] for r in rows if r.get("top1_correct")][:10],
        }
    total = sum(v["sample_count"] for v in by_stage.values())
    success = sum(int(v["top1_correct_rate"] * v["sample_count"]) for v in by_stage.values())
    return {"by_stage": by_stage, "heldout_supported_success_rate": _rate(success, total)}


def _rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0
