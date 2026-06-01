from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List


def verify_contrastive_pairs(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["pair_id"])].append(row)
    complete = 0
    verified = 0
    expected_diff = 0
    same_output = 0
    for items in grouped.values():
        roles = {row.get("pair_role") for row in items}
        if {"anchor", "positive_equivalent", "negative_minimal_diff"}.issubset(roles):
            complete += 1
            anchor = next(row for row in items if row["pair_role"] == "anchor")
            positive = next(row for row in items if row["pair_role"] == "positive_equivalent")
            negative = next(row for row in items if row["pair_role"] == "negative_minimal_diff")
            if anchor.get("expected_output") == positive.get("expected_output"):
                same_output += 1
            if anchor.get("expected_output") != negative.get("expected_output"):
                expected_diff += 1
            if anchor.get("semantic_hash") != negative.get("semantic_hash"):
                verified += 1
    total = max(len(grouped), 1)
    return {
        "total_pairs": len(grouped),
        "complete_pair_count": complete,
        "pair_integrity_passed": complete == len(grouped) and len(grouped) > 0,
        "pair_semantic_difference_verified_rate": round(verified / total, 6),
        "pair_expected_output_difference_rate": round(expected_diff / total, 6),
        "same_semantics_output_same_rate": round(same_output / total, 6),
    }
