from __future__ import annotations

from typing import Any, Dict


def assess_v0_9_1_readiness(summary: Dict[str, Any]) -> Dict[str, Any]:
    blockers = []
    if "large" not in summary.get("modes_completed", []):
        blockers.append("large mode not completed")
    if summary.get("persisted_state_support_level") != "full_router_root":
        blockers.append("persisted_state_support_level is not full_router_root")
    if summary.get("missing_for_full_state") not in ([], None):
        blockers.append("missing_for_full_state is not empty")
    if summary.get("forbidden_field_in_state_count", 1) != 0:
        blockers.append("forbidden fields found in state")
    if summary.get("cross_process_reload_passed") is not True:
        blockers.append("cross_process_reload_passed is not true")
    if summary.get("multi_seed_stable") is not True:
        blockers.append("multi_seed_stable is not true")
    if summary.get("expanded_external_ood_completed") is not True:
        blockers.append("expanded external OOD was not completed")
    if float(summary.get("external_ood_false_accept_rate", 1.0)) > 0.10:
        blockers.append("external_ood_false_accept_rate exceeds 0.10")
    if float(summary.get("supported_retention_rate", 0.0)) < 0.98:
        blockers.append("supported_retention_rate below 0.98")
    if summary.get("baseline_harness_generated") is not True:
        blockers.append("baseline harness not generated")
    if summary.get("ablation_harness_generated") is not True:
        blockers.append("ablation harness not generated")
    if summary.get("comparison_data_pack_generated") is not True:
        blockers.append("comparison data pack not generated")
    if summary.get("real_promotion_disabled") is not True:
        blockers.append("real promotion not confirmed disabled")

    ready = not blockers
    if ready:
        level = "large_completed_strong_signal"
    elif summary.get("modes_completed"):
        level = "partial_scale_signal"
    else:
        level = "failed"
    return {
        "ready_for_v0_9_1_claim": ready,
        "recommended_claim_level": level,
        "blocking_issues": blockers,
        "required_non_claims": [
            "stable convergence",
            "solved OOD",
            "solved arithmetic",
            "general program synthesis",
            "same-size LLM advantage",
            "safe real promotion",
            "production readiness",
        ],
    }
