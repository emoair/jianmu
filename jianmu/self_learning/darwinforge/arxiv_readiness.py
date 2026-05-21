from __future__ import annotations

from typing import Dict, List


REQUIRED_NON_CLAIMS = [
    "no stable convergence claim",
    "no solved arithmetic claim",
    "no solved OOD claim",
    "no general program synthesis claim",
    "no AGI claim",
    "no Transformer replacement claim",
    "no same-size LLM advantage claim",
    "no safe real promotion claim",
]


def assess_arxiv_readiness(v087_summary: Dict, persisted_eval: Dict, external_ood: Dict, multiseed: Dict, consistency: Dict) -> Dict:
    blocking: List[str] = []
    if persisted_eval.get("reloaded_eval_completed") is not True:
        blocking.append("reloaded eval did not complete")
    if persisted_eval.get("no_label_inference_passed") is not True:
        blocking.append("no-label guard failed")
    if consistency.get("persisted_state_consistency_passed") is not True:
        blocking.append("persisted state consistency failed")
    if external_ood.get("metrics", {}).get("overall_ood_false_accept_rate", 1.0) > 0.10:
        blocking.append("external OOD false accept above 0.10")
    if persisted_eval.get("current_supported_retention_rate", 0.0) < 0.98:
        blocking.append("supported retention below 0.98")
    if multiseed.get("stable_across_seeds") is not True:
        blocking.append("multi-seed stability not established")
    if persisted_eval.get("persisted_state_support_level") == "summary_only":
        blocking.append("persisted state support is summary_only, not full router/root state")

    ready = not blocking
    return {
        "ready_for_arxiv_technical_report": ready,
        "recommended_claim_level": "technical_report_candidate" if ready else "needs_more_validation",
        "blocking_issues": blocking,
        "recommended_title": "JianMu: Nutrient-Guided Root-Colony Routing for Compiler-Verified Program Synthesis",
        "required_non_claims": REQUIRED_NON_CLAIMS,
        "suggested_next_experiments": [
            "full router/root state persistence",
            "external OOD from independently authored sources",
            "more seeds and larger free-beam runs",
            "same-size LLM / Transformer baseline",
        ],
        "v0_8_7_reference_available": bool(v087_summary),
    }
