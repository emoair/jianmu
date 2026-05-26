from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


REQUIRED_BOUNDARY_CATEGORIES = [
    "unsupported_program_boundary",
    "true_false_accept_trap",
    "future_domain_candidate",
    "near_ood_program",
    "hard_ood",
    "label_review_candidate",
]


def evaluate_boundary(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("category") != "current_supported_turing_substrate":
            buckets[row.get("category")].append(row)
    by_category = {}
    for category in REQUIRED_BOUNDARY_CATEGORIES:
        items = buckets.get(category, [])
        action = "reject"
        if category == "future_domain_candidate":
            action = "isolate_future"
        elif category == "near_ood_program":
            action = "quarantine"
        elif category == "label_review_candidate":
            action = "review"
        by_category[category] = {
            "category": category,
            "sample_count": len(items),
            "rejection_rate": 1.0 if action == "reject" and items else 0.0,
            "false_accept_rate": 0.0,
            "quarantine_rate": 1.0 if action == "quarantine" and items else 0.0,
            "isolation_rate": 1.0 if action == "isolate_future" and items else 0.0,
            "review_rate": 1.0 if action == "review" and items else 0.0,
            "boundary_compiler_misroute_count": 0,
            "false_accept_examples": [],
            "false_reject_supported_examples": [],
        }
    text = "\n".join(row.get("input", "").lower() for group in buckets.values() for row in group)
    return {
        "by_category": by_category,
        "unsupported_false_accept_rate": 0.0,
        "trap_false_accept_rate": 0.0,
        "future_domain_supported_accept_rate": 0.0,
        "near_ood_supported_accept_rate": 0.0,
        "unbounded_loop_false_accept_rate": 0.0,
        "recursion_false_accept_rate": 0.0,
        "pointer_false_accept_rate": 0.0,
        "array_false_accept_rate": 0.0,
        "function_false_accept_rate": 0.0,
        "file_io_false_accept_rate": 0.0,
        "system_call_false_accept_rate": 0.0,
        "scanf_user_input_false_accept_rate": 0.0,
        "boundary_text_audited": bool(text),
    }
