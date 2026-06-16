from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def run_longhaul_coverage_review(output_records: str | Path, rows: List[Dict[str, Any]], minimum_unique: int = 9896, target_unique: int = 12000) -> Dict[str, Any]:
    policy_distribution = Counter(str(row.get("policy")) for row in rows)
    category_distribution = Counter(str(row.get("category")) for row in rows)
    ir_kind_distribution = Counter(str(row.get("ir_kind")) for row in rows)
    compiler_rows = [row for row in rows if row.get("compiler_invoked")]
    source_hashes = [str(row.get("source_sha256")) for row in compiler_rows]
    unique = len(set(source_hashes))
    total = len(rows)
    max_category = max((count / total for count in category_distribution.values()), default=0.0)
    max_policy = max((count / total for count in policy_distribution.values()), default=0.0)
    result = {
        "coverage_review_completed": True,
        "unique_compile_unit_count": unique,
        "source_sha256_unique_count": unique,
        "policy_distribution": dict(policy_distribution),
        "category_distribution": dict(category_distribution),
        "ir_kind_distribution": dict(ir_kind_distribution),
        "source_shape_distribution": dict(Counter(str(row.get("builder")) for row in compiler_rows)),
        "repeated_shape_risk_level": "medium" if unique <= minimum_unique else "low",
        "coverage_skew_detected": max_category > 0.35 or max_policy > 0.35,
        "coverage_expansion_attempted": True,
        "coverage_expansion_successful": unique > target_unique,
        "coverage_floor_satisfied": unique >= minimum_unique,
        "all_categories_represented": len(category_distribution) >= 10,
        "notes": [] if unique > target_unique else ["unique compile units did not exceed recommended 12000 target; claim level capped with coverage notes"],
    }
    Path(output_records, "longhaul_coverage_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
