from __future__ import annotations

from typing import Dict, List


REQUIRED_NON_CLAIMS = [
    "no stable convergence claim",
    "no solved OOD claim",
    "no solved arithmetic claim",
    "no general program synthesis claim",
    "no same-size LLM advantage claim",
    "no safe real promotion claim",
]


def assess_arxiv_readiness_v2(full_state_eval: Dict, external_ood: Dict, multiseed: Dict, consistency: Dict, forbidden_scan: Dict) -> Dict:
    blocking: List[str] = []
    support_level = full_state_eval.get("persisted_state_support_level", "unavailable")
    if support_level != "full_router_root":
        blocking.append(f"persisted_state_support_level is {support_level}, not full_router_root")
    if consistency.get("full_state_consistency_passed") is not True:
        blocking.append("full state consistency failed")
    if full_state_eval.get("cross_process_reload_passed") is not True:
        blocking.append("cross-process reload eval did not pass")
    if external_ood.get("overall_ood_false_accept_rate", 1.0) > 0.10:
        blocking.append("external OOD false accept above 0.10")
    if full_state_eval.get("current_supported_retention_rate", 0.0) < 0.98:
        blocking.append("supported retention below 0.98")
    if multiseed.get("stable_across_seeds") is not True:
        blocking.append("multi-seed stability not established")
    if forbidden_scan.get("forbidden_field_in_state_count", 1) > 0:
        blocking.append("forbidden fields found in state")
    if full_state_eval.get("hardcoded_rejection_gate_added") is True:
        blocking.append("hard-coded rejection gate detected")
    if full_state_eval.get("real_promotion_enabled") is True:
        blocking.append("real promotion enabled")
    ready = not blocking
    return {
        "ready_for_arxiv_technical_report": ready,
        "recommended_claim_level": "technical_report_candidate" if ready else "needs_more_validation",
        "blocking_issues": blocking,
        "recommended_title": "JianMu: Nutrient-Guided Root-Colony Routing for Compiler-Verified Program Synthesis",
        "recommended_abstract_boundary": "Claim bounded persisted-state and external-OOD evidence only if support_level is full_router_root; otherwise report persistence as partial.",
        "required_non_claims": REQUIRED_NON_CLAIMS,
        "suggested_next_experiments": [
            "capture trained BranchChain population objects",
            "capture trained Root Colony lifecycle state",
            "rerun cross-process external OOD with full_router_root state",
            "same-size LLM / Transformer baseline",
        ],
    }
