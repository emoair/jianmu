from __future__ import annotations

from typing import Any, Dict, List


def assess_compiler_longrun_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    backend_type = metrics.get("backend_type", "unavailable")
    invocations = int(metrics.get("real_compiler_invocation_count") or 0)
    correct_rate = metrics.get("compiler_verified_correct_rate")
    fresh_ratio = float(metrics.get("fresh_longrun_ratio") or 0.0)
    failures = int(metrics.get("compiler_verified_failure_count") or 0)
    longrun_partial = any(item.get("mode") == "longrun" for item in metrics.get("modes_partial_skipped", []))

    if backend_type != "real_c_compiler":
        claim = "compiler_unavailable"
        blocking.append("real_compiler_unavailable")
    else:
        if invocations <= 0:
            blocking.append("real_compiler_not_invoked")
        if fresh_ratio < 0.90:
            blocking.append("fresh_longrun_ratio_below_threshold")
        if metrics.get("boundary_compiler_misroute_count", 0) != 0:
            blocking.append("boundary_compiler_misroute_detected")
        if metrics.get("forbidden_field_access_count", 0) != 0:
            blocking.append("forbidden_field_access_detected")
        if not metrics.get("backend_claim_safe", False):
            blocking.append("backend_claim_not_safe")

        if blocking:
            claim = "failed"
        elif failures and failures / max(invocations, 1) > 0.02:
            claim = "needs_failure_taxonomy"
        elif longrun_partial:
            claim = "compiler_backed_arithmetic_partial_longrun"
        elif invocations >= 20000 and correct_rate is not None and correct_rate >= 0.98:
            claim = "compiler_backed_arithmetic_longrun_signal"
        elif invocations >= 5000 and correct_rate is not None and correct_rate >= 0.98:
            claim = "compiler_backed_arithmetic_medium_signal"
        elif failures:
            claim = "needs_failure_taxonomy"
        else:
            claim = "failed"

    required = []
    if backend_type != "real_c_compiler":
        required.append("run from MSVC-enabled environment")
    if claim in {"compiler_backed_arithmetic_medium_signal", "compiler_backed_arithmetic_partial_longrun"}:
        required.append("complete larger compiler-backed longrun")
    if claim == "needs_failure_taxonomy":
        required.append("run compiler failure taxonomy on longrun failures")
    required.append("maintain conservative arithmetic and Turing-completeness wording")

    return {
        "longrun_readiness_completed": bool(metrics.get("modes_completed")),
        "backend_type": backend_type,
        "compiler_name": metrics.get("compiler_name", ""),
        "compiler_environment": metrics.get("compiler_environment", ""),
        "real_compiler_invocation_count": invocations,
        "compiler_verified_correct_rate": correct_rate,
        "fresh_longrun_ratio": fresh_ratio,
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count", 0),
        "backend_claim_safe": bool(metrics.get("backend_claim_safe")),
        "recommended_claim_level": claim,
        "blocking_issues": sorted(set(blocking)),
        "required_next_run": "; ".join(required),
    }
