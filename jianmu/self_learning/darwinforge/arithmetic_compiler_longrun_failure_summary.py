from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_compiler_failure_taxonomy import classify_compiler_failure


def summarize_longrun_failures(trace_rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    failures = []
    for row in trace_rows:
        if row.get("category") != "current_supported_arithmetic":
            continue
        if (
            row.get("compile_success") is False
            or row.get("runtime_success") is False
            or row.get("compiler_verified_correct") is False
            or row.get("timeout") is True
            or row.get("unsafe_expression") is True
        ):
            category = classify_compiler_failure(row, row)
            failure = dict(row)
            failure["failure_category"] = category
            failures.append(failure)
    counts = Counter(row["failure_category"] for row in failures)
    return {
        "failure_count": len(failures),
        "failure_category_distribution": dict(sorted(counts.items())),
        "failure_examples": failures[:100],
    }
