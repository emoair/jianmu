from __future__ import annotations

from typing import Any, Dict


def analyze_project_failures(metrics: Dict[str, Any]) -> Dict[str, Any]:
    failures = []
    if metrics.get("project_parse_success_rate", 1.0) < 0.9:
        failures.append("project_parse")
    if metrics.get("token_schema_valid_rate", 1.0) < 0.98:
        failures.append("token_schema")
    return {"failure_categories": failures, "needs_failure_taxonomy": bool(failures)}

