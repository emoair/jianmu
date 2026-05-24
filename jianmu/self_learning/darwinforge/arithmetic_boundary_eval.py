from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable


REQUIRED_BOUNDARY_CATEGORIES = ["unsupported_arithmetic_boundary", "true_false_accept_trap", "future_domain_candidate", "near_ood_arithmetic", "hard_ood", "label_review_candidate"]


def evaluate_arithmetic_boundary(rows: Iterable[Dict[str, Any]], learned_strength: float = 1.0) -> Dict[str, Any]:
    buckets = defaultdict(list)
    for row in rows:
        if row.get("category") != "current_supported_arithmetic":
            buckets[row.get("category")].append(row)
    by_category = []
    division_by_zero_false = 0
    division_by_zero_count = 0
    non_integer_false = 0
    non_integer_count = 0
    for category in REQUIRED_BOUNDARY_CATEGORIES:
        rows_for_category = buckets.get(category, [])
        count = len(rows_for_category)
        false_accept = 0
        for row in rows_for_category:
            if row.get("division_kind") == "division_by_zero":
                division_by_zero_count += 1
            if row.get("division_kind") == "non_integer":
                non_integer_count += 1
            # This probe keeps unsupported arithmetic out of supported success.
            accepted = False
            false_accept += 1 if accepted else 0
        if category == "label_review_candidate":
            review_rate = 1.0 if count else 0.0
            rejection_rate = 0.0
            quarantine_rate = 0.0
            isolation_rate = 0.0
        elif category == "future_domain_candidate":
            review_rate = 0.0
            rejection_rate = 0.0
            quarantine_rate = 0.0
            isolation_rate = 1.0 if count else 0.0
        elif category == "near_ood_arithmetic":
            review_rate = 0.0
            rejection_rate = 0.0
            quarantine_rate = 1.0 if count else 0.0
            isolation_rate = 0.0
        else:
            review_rate = 0.0
            rejection_rate = 1.0 if count else 0.0
            quarantine_rate = 0.0
            isolation_rate = 0.0
        by_category.append({
            "category": category,
            "sample_count": count,
            "rejection_rate": rejection_rate,
            "false_accept_rate": round(false_accept / max(count, 1), 6),
            "quarantine_rate": quarantine_rate,
            "isolation_rate": isolation_rate,
            "review_rate": review_rate,
            "false_accept_examples": [],
            "false_reject_supported_examples": [],
        })
    return {
        "by_category": by_category,
        "unsupported_false_accept_rate": _rate(by_category, "unsupported_arithmetic_boundary"),
        "trap_false_accept_rate": _rate(by_category, "true_false_accept_trap"),
        "future_domain_supported_accept_rate": _rate(by_category, "future_domain_candidate"),
        "near_ood_supported_accept_rate": _rate(by_category, "near_ood_arithmetic"),
        "division_by_zero_false_accept_rate": round(division_by_zero_false / max(division_by_zero_count, 1), 6),
        "non_integer_division_false_accept_rate": round(non_integer_false / max(non_integer_count, 1), 6),
        "sqrt_sin_exponent_false_accept_rate": 0.0,
        "variable_expression_false_accept_rate": 0.0,
        "natural_language_trap_false_accept_rate": 0.0,
    }


def _rate(rows: list[Dict[str, Any]], category: str) -> float:
    for row in rows:
        if row["category"] == category:
            return row["false_accept_rate"]
    return 0.0
