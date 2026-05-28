from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def assess_clean_validation_readiness(
    output_records: str | Path,
    preflight: Dict[str, Any],
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    primary = metrics.get("primary", {})
    fallback = metrics.get("fallback", {})
    blockers = []
    if not preflight.get("preflight_passed"):
        blockers.extend(preflight.get("preflight_blocking_issues", []))
    if primary.get("executed") and primary.get("permission_error_count", 0):
        blockers.append("primary permission/process-spawn instability detected")
    if primary.get("executed") and primary.get("completed") and primary.get("compiler_verified_correct_rate", 0.0) < 0.98:
        blockers.append("primary compiler verified rate below threshold")
    if fallback.get("executed") and fallback.get("permission_error_count", 0):
        blockers.append("fallback permission/process-spawn instability detected")
    if primary.get("completed") and _pass_run(primary):
        claim = "independent_compiler_validation_restored"
    elif fallback.get("completed") and _pass_run(fallback):
        claim = "independent_compiler_validation_restored_with_fallback"
    elif preflight.get("preflight_passed") and (primary.get("permission_error_count", 0) or fallback.get("permission_error_count", 0)):
        claim = "independent_validation_still_unstable"
    elif not preflight.get("cl_bv_test_passed"):
        claim = "compiler_unavailable"
    else:
        claim = "failed"
    readiness = {
        "preflight_passed": preflight.get("preflight_passed", False),
        "primary_independent_validation_executed": primary.get("executed", False),
        "primary_independent_validation_completed": primary.get("completed", False),
        "primary_permission_error_count": primary.get("permission_error_count", 0),
        "primary_compiler_verified_correct_rate": primary.get("compiler_verified_correct_rate", 0.0),
        "fallback_executed": fallback.get("executed", False),
        "fallback_completed": fallback.get("completed", False),
        "fallback_permission_error_count": fallback.get("permission_error_count", 0),
        "fallback_compiler_verified_correct_rate": fallback.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count": primary.get("boundary_compiler_misroute_count", 0) + fallback.get("boundary_compiler_misroute_count", 0),
        "backend_claim_safe": primary.get("backend_claim_safe", False) or fallback.get("backend_claim_safe", False),
        "original_v0_9_7_1_result_preserved": True,
        "patched_v0_9_7_2_result_preserved": True,
        "recommended_claim_level": claim,
        "blocking_issues": blockers,
        "required_next_run": "full-level bounded substrate compiler validation can continue; still no Turing-completeness claim" if claim.startswith("independent_compiler_validation_restored") else "rerun from clean MSVC shell after resolving preflight or process-spawn issues",
    }
    Path(output_records).mkdir(parents=True, exist_ok=True)
    (Path(output_records) / "clean_validation_readiness.json").write_text(json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return readiness


def _pass_run(row: Dict[str, Any]) -> bool:
    return (
        row.get("real_compiler_invocation_count", 0) > 0
        and row.get("permission_error_count", 0) == 0
        and row.get("compiler_verified_correct_rate", 0.0) >= 0.98
        and row.get("boundary_compiler_misroute_count", 0) == 0
        and row.get("backend_claim_safe", False)
    )
