from __future__ import annotations

from typing import Any, Dict


FORBIDDEN_COUNT_FIELDS = [
    "wrong_stdout_count",
    "timeout_count",
    "permission_error_count",
    "cleanup_failure_count",
    "boundary_compiler_misroute_count",
    "future_domain_compiled_count",
    "unsupported_compiled_count",
    "trap_compiled_count",
    "english_compiled_count",
    "mixed_language_compiled_count",
    "recursion_compiled_count",
    "pointer_compiled_count",
    "io_compiled_count",
]


def clean_observed(row: Dict[str, Any], threshold: float = 0.995) -> bool:
    return row.get("compiler_verified_correct_rate", 0.0) >= threshold and all(int(row.get(key, 0)) == 0 for key in FORBIDDEN_COUNT_FIELDS)


def reconcile_claim(
    original_claim_level: str,
    gate_completed: bool,
    gate_clean: bool,
    main_completed: bool,
    main_clean: bool,
    extended_completed: bool,
    extended_completed_clean: bool,
    accounting_passed: bool,
    fields_consistent: bool,
) -> Dict[str, Any]:
    if not accounting_passed or not fields_consistent:
        claim = "ironjudge_not_clean_needs_failure_taxonomy"
    elif extended_completed and extended_completed_clean:
        claim = "ironjudge_50k_clean_frontier_evidence_reconciled"
    elif main_completed and main_clean:
        claim = "ironjudge_20k_clean_frontier_evidence_reconciled"
    elif gate_completed and gate_clean:
        claim = "ironjudge_5k_clean_needs_20k_reconciled"
    else:
        claim = "ironjudge_not_clean_needs_failure_taxonomy"

    return {
        "original_claim_level": original_claim_level,
        "recommended_claim_level": claim,
        "v0_9_18_claim_upgrade_supported": claim in {
            "ironjudge_50k_clean_frontier_evidence_reconciled",
            "ironjudge_20k_clean_frontier_evidence_reconciled",
        },
        "v0_9_18_1_claim_was_overstated": original_claim_level == "ironjudge_20k_clean_frontier_evidence_strengthened" and not (main_completed and main_clean),
        "final_claim_consistent_with_fields": fields_consistent and (claim != "ironjudge_20k_clean_frontier_evidence_reconciled" or (main_completed and main_clean)),
        "blocking_issues": [] if claim == "ironjudge_20k_clean_frontier_evidence_reconciled" else ["main_20k_not_completed_clean"],
        "required_next_run": "optional extended_50k continuation" if claim == "ironjudge_20k_clean_frontier_evidence_reconciled" else "complete main_20k or downgrade IronJudge claim",
    }
