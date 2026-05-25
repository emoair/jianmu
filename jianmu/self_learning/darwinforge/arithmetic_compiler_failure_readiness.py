from __future__ import annotations

from typing import Any, Dict, List


def assess_compiler_failure_readiness(summary: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    original_failure_count = int(summary.get("original_failure_count", 0))
    classified = int(summary.get("classified_failure_count", 0))
    unknown = int(summary.get("unknown_failure_count", 0))
    engineering = bool(summary.get("engineering_issue_dominant"))
    candidate = bool(summary.get("candidate_error_dominant"))
    patched = bool(summary.get("patched_rerun_executed"))
    patched_delta = float(summary.get("patched_delta_vs_original") or 0.0)
    remaining = int(summary.get("patched_remaining_failure_count", original_failure_count))

    if original_failure_count <= 0:
        blocking.append("no_original_failures_to_classify")
    if classified != original_failure_count:
        blocking.append("classified_failure_count_mismatch")
    if unknown > max(1, original_failure_count // 4):
        blocking.append("too_many_unknown_failures")
    if not summary.get("original_result_preserved", False):
        blocking.append("original_result_not_preserved")

    if blocking:
        claim = "failed"
    elif patched and patched_delta > 0 and remaining < original_failure_count:
        claim = "compiler_backed_signal_strengthened_after_patch"
    elif engineering:
        claim = "compiler_backed_signal_with_engineering_failures_explained"
    elif candidate and remaining > 0:
        claim = "compiler_backed_signal_with_candidate_failures"
    elif candidate:
        claim = "needs_candidate_generation_fix"
    else:
        claim = "compiler_backed_signal_with_engineering_failures_explained"

    required = []
    if remaining > 0:
        required.append("rerun remaining compiler failures with expanded stderr capture")
    if candidate:
        required.append("inspect candidate expressions for arithmetic generation errors")
    required.append("full compiler-backed longrun remains open")

    return {
        "failure_taxonomy_completed": classified == original_failure_count and original_failure_count > 0,
        "original_failure_count": original_failure_count,
        "classified_failure_count": classified,
        "unknown_failure_count": unknown,
        "dominant_failure_category": summary.get("dominant_failure_category", "unknown"),
        "engineering_issue_dominant": engineering,
        "candidate_error_dominant": candidate,
        "patched_rerun_executed": patched,
        "patched_compiler_verified_correct_rate": summary.get("patched_compiler_verified_correct_rate"),
        "remaining_failure_count": remaining,
        "claim_level_before": "compiler_backed_arithmetic_spot_signal",
        "claim_level_after": claim,
        "recommended_claim_level": claim,
        "blocking_issues": sorted(set(blocking)),
        "required_next_run": "; ".join(required),
    }
