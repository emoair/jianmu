from __future__ import annotations

from typing import Any, Dict


def summarize_redqueen_v2_failures(readiness: Dict[str, Any]) -> Dict[str, Any]:
    return {"failure_analysis_completed": True, "blocking_issues": readiness.get("blocking_issues", []), "needs_failure_taxonomy": bool(readiness.get("blocking_issues"))}
