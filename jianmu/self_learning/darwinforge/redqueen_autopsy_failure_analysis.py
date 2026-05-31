from __future__ import annotations

from typing import Any, Dict, List


def summarize_redqueen_autopsy_failures(readiness: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = list(readiness.get("blocking_issues", []))
    return {
        "failure_analysis_completed": True,
        "blocking_issues": blocking,
        "requires_more_attribution": readiness.get("recommended_claim_level") == "redqueen_autopsy_mixed_needs_more_attribution",
        "notes": ["No capability gain is claimed by this autopsy."],
    }
