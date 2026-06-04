from __future__ import annotations

from typing import Any, Dict


def analyze_algorithm_failures(metrics: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if metrics.get("algorithm_parse_success_rate", 1.0) < 0.9:
        failures.append("algorithm_parse")
    if metrics.get("compiler_verified_correctness_rate", 1.0) < 1.0:
        failures.append("compiler_validation")
    return {"failure_categories": failures, "needs_failure_taxonomy": bool(failures)}

