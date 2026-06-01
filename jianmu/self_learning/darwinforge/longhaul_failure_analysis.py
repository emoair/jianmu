from __future__ import annotations

from typing import Any, Dict


def analyze_longhaul_failures(readiness: Dict[str, Any]) -> Dict[str, Any]:
    blocking = list(readiness.get("blocking_issues", []))
    return {
        "failure_analysis_completed": True,
        "blocking_issues": blocking,
        "dominant_failure": blocking[0] if blocking else None,
        "needs_failure_taxonomy": bool(blocking),
    }


__all__ = ["analyze_longhaul_failures"]
