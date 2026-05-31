from __future__ import annotations

from typing import Any, Dict, Iterable


FAILURE_CATEGORIES = [
    "permission_error",
    "cleanup_failure",
    "process_spawn_error",
    "timeout",
    "wrong_stdout",
    "compile_syntax_error",
    "runtime_error",
    "boundary_misroute",
    "future_domain_compiled",
    "unknown",
]


def classify_ironjudge_failures(traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    distribution = {key: 0 for key in FAILURE_CATEGORIES}
    for row in traces:
        if row.get("compiler_verified_correct") or not row.get("compiler_invoked"):
            continue
        if row.get("timeout"):
            distribution["timeout"] += 1
        elif row.get("compile_success") is False:
            distribution["compile_syntax_error"] += 1
        elif row.get("runtime_success") is False:
            distribution["runtime_error"] += 1
        else:
            distribution["wrong_stdout"] += 1
    failures = sum(distribution.values())
    return {"failure_category_distribution": distribution, "classified_failure_count": failures, "unknown_failure_count": distribution["unknown"]}
