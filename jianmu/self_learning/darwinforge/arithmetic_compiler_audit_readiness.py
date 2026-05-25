from __future__ import annotations

from typing import Any, Dict, List


def assess_compiler_audit_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    backend_type = metrics.get("backend_type", "unavailable")
    if not metrics.get("audit_completed"):
        blocking.append("audit_not_completed")
    if metrics.get("forbidden_field_access_count", 0) != 0:
        blocking.append("forbidden_field_access_detected")
    if not metrics.get("backend_claim_safe"):
        blocking.append("backend_claim_not_safe")
    if metrics.get("boundary_compiler_misroute_count", 0) != 0:
        blocking.append("boundary_compiler_misroute_detected")

    if backend_type == "real_c_compiler":
        if metrics.get("real_compiler_invocation_count", 0) <= 0:
            blocking.append("real_compiler_not_invoked")
        if metrics.get("compiler_spot_sample_count", 0) <= 0:
            blocking.append("no_compiler_spot_samples")
        if metrics.get("compiler_verified_correct_rate") is None:
            blocking.append("compiler_verified_rate_missing")
        if blocking:
            claim = "failed"
        else:
            claim = "compiler_backed_arithmetic_spot_signal"
    elif backend_type == "python_subprocess_executor":
        claim = "execution_backed_but_not_compiler"
        blocking.append("real_c_compiler_unavailable")
    elif backend_type == "internal_evaluator":
        claim = "internal_evaluator_only"
        blocking.append("real_c_compiler_unavailable")
    elif backend_type == "unavailable":
        claim = "compiler_unavailable"
        blocking.append("no_external_execution_backend")
    else:
        claim = "failed"
        blocking.append("unknown_backend_type")

    required = []
    if backend_type != "real_c_compiler":
        required.append("install or enable gcc, clang, or cl and rerun compiler spot audit")
    required.append("full compiler-backed longrun remains open")

    return {
        "audit_completed": bool(metrics.get("audit_completed")),
        "real_compiler_available": backend_type == "real_c_compiler",
        "backend_type": backend_type,
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count", 0),
        "compiler_backed_spot_verified": claim == "compiler_backed_arithmetic_spot_signal",
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate"),
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count", 0),
        "forbidden_field_access_count": metrics.get("forbidden_field_access_count", 0),
        "backend_claim_safe": bool(metrics.get("backend_claim_safe")),
        "recommended_claim_level": claim,
        "blocking_issues": sorted(set(blocking)),
        "required_next_run": "; ".join(required),
    }
