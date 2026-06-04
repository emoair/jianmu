from __future__ import annotations

from typing import Any, Dict


def analyze_linguaforge_failures(metrics: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if metrics.get("nl_direct_code_generation_count", 0):
        issues.append("direct_code_generation")
    if metrics.get("token_schema_valid_rate", 1.0) < 0.98:
        issues.append("token_schema")
    return {"failure_categories": issues, "needs_taxonomy": bool(issues)}

