from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def assess_permission_failure_readiness(
    output_records: str | Path,
    taxonomy: Dict[str, Any],
    patched: Dict[str, Any],
    independent: Dict[str, Any],
) -> Dict[str, Any]:
    blockers = []
    if not taxonomy.get("taxonomy_completed"):
        blockers.append("taxonomy incomplete")
    if patched.get("patched_permission_error_count", 0) != 0:
        blockers.append("patched replay still has permission errors")
    if independent.get("permission_error_count", 0) != 0:
        blockers.append("independent validation still has permission errors")
    if independent.get("compiler_verified_correct_rate", 0.0) < 0.98:
        blockers.append("independent compiler verified correct rate below 0.98")
    if independent.get("boundary_compiler_misroute_count", 0) != 0:
        blockers.append("boundary compiler misroute detected")
    if (
        taxonomy.get("taxonomy_completed")
        and taxonomy.get("engineering_issue_dominant")
        and patched.get("patched_permission_error_count", 1) == 0
        and independent.get("permission_error_count", 1) == 0
        and independent.get("compiler_verified_correct_rate", 0.0) >= 0.98
        and independent.get("boundary_compiler_misroute_count", 0) == 0
        and patched.get("original_result_preserved")
    ):
        claim = "compiler_permission_failures_explained_and_fixed"
    elif taxonomy.get("engineering_issue_dominant") and patched.get("patched_compiler_verified_correct_rate", 0.0) > 0:
        claim = "compiler_permission_failures_explained_but_partial_fix"
    elif taxonomy.get("candidate_error_dominant"):
        claim = "candidate_or_program_errors_detected"
    elif blockers:
        claim = "needs_toolchain_fix"
    else:
        claim = "failed"
    readiness = {
        "taxonomy_completed": taxonomy.get("taxonomy_completed", False),
        "original_failure_count": taxonomy.get("original_failure_count", 0),
        "classified_failure_count": taxonomy.get("classified_failure_count", 0),
        "unknown_failure_count": taxonomy.get("unknown_failure_count", 0),
        "dominant_failure_category": taxonomy.get("dominant_failure_category", "unknown"),
        "engineering_issue_dominant": taxonomy.get("engineering_issue_dominant", False),
        "candidate_error_dominant": taxonomy.get("candidate_error_dominant", False),
        "patched_replay_executed": patched.get("patched_replay_sample_count", 0) > 0,
        "patched_permission_error_count": patched.get("patched_permission_error_count", 0),
        "patched_compiler_verified_correct_rate": patched.get("patched_compiler_verified_correct_rate", 0.0),
        "independent_validation_executed": independent.get("supported_sample_count", 0) > 0,
        "independent_permission_error_count": independent.get("permission_error_count", 0),
        "independent_compiler_verified_correct_rate": independent.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count": independent.get("boundary_compiler_misroute_count", 0),
        "temp_manager_fix_applied": True,
        "original_result_preserved": patched.get("original_result_preserved", False),
        "claim_level_before": "needs_failure_taxonomy",
        "claim_level_after": claim,
        "recommended_claim_level": claim,
        "blocking_issues": blockers,
        "required_next_run": "rerun bounded substrate full-level compiler validation after temp manager fix; still no Turing-completeness claim",
    }
    Path(output_records).mkdir(parents=True, exist_ok=True)
    (Path(output_records) / "permission_failure_readiness.json").write_text(json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return readiness
