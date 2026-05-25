from __future__ import annotations

from typing import Any, Dict, List


def assess_fresh_compiler_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    backend_type = metrics.get("backend_type", "unavailable")
    correct_rate = metrics.get("compiler_verified_correct_rate")
    fresh_ratio = float(metrics.get("fresh_ratio") or 0.0)

    if backend_type != "real_c_compiler":
        claim = "compiler_unavailable"
        blocking.append("real_compiler_unavailable")
    else:
        if metrics.get("real_compiler_invocation_count", 0) <= 0:
            blocking.append("real_compiler_not_invoked")
        if fresh_ratio < 0.90:
            blocking.append("fresh_ratio_below_threshold")
        if metrics.get("boundary_compiler_misroute_count", 0) != 0:
            blocking.append("boundary_compiler_misroute_detected")
        if metrics.get("forbidden_field_access_count", 0) != 0:
            blocking.append("forbidden_field_access_detected")
        if not metrics.get("backend_claim_safe", False):
            blocking.append("backend_claim_not_safe")

        if blocking:
            claim = "failed"
        elif correct_rate is not None and correct_rate >= 0.98:
            claim = "fresh_compiler_backed_arithmetic_signal_reproduced"
        elif correct_rate is not None and correct_rate >= 0.80:
            claim = "fresh_compiler_backed_arithmetic_signal_mixed"
        else:
            claim = "needs_compiler_failure_taxonomy"

    required = []
    if backend_type != "real_c_compiler":
        required.append("run from MSVC-enabled environment")
    if claim in {"fresh_compiler_backed_arithmetic_signal_mixed", "needs_compiler_failure_taxonomy"}:
        required.append("run compiler failure taxonomy on fresh failures")
    required.append("full compiler-backed longrun remains open")

    return {
        "fresh_reproduction_completed": bool(metrics.get("modes_completed")),
        "real_compiler_available": backend_type == "real_c_compiler",
        "backend_type": backend_type,
        "compiler_name": metrics.get("compiler_name", ""),
        "compiler_environment": metrics.get("compiler_environment", ""),
        "fresh_ratio": fresh_ratio,
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count", 0),
        "compiler_verified_correct_rate": correct_rate,
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count", 0),
        "token_spacing_patch_enabled": bool(metrics.get("token_spacing_patch_enabled")),
        "backend_claim_safe": bool(metrics.get("backend_claim_safe")),
        "recommended_claim_level": claim,
        "blocking_issues": sorted(set(blocking)),
        "required_next_run": "; ".join(required),
    }
