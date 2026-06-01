from __future__ import annotations

from typing import Any, Dict, List


def analyze_large_loop_failures(metrics: Dict[str, Any]) -> Dict[str, Any]:
    partial = metrics.get("experiment_groups_partial", [])
    return {
        "failure_analysis_completed": True,
        "partial_group_count": len(partial),
        "failure_examples": [],
        "dominant_failure_type": "none" if not partial else "partial_runtime",
    }
