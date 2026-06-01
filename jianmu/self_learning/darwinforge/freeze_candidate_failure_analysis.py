from __future__ import annotations

from typing import Any, Dict


def analyze_freeze_candidate_failures(readiness: Dict[str, Any]) -> Dict[str, Any]:
    blocking = list(readiness.get("blocking_issues", []))
    return {
        "failure_analysis_completed": True,
        "blocking_issues": blocking,
        "dominant_failure": blocking[0] if blocking else None,
        "requires_evidence_fix": any("evidence" in item or "compiler" in item for item in blocking),
        "requires_claim_cleanup": any("claim" in item for item in blocking),
    }


__all__ = ["analyze_freeze_candidate_failures"]
