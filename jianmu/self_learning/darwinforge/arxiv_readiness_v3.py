from __future__ import annotations

from typing import Dict, List


def assess_arxiv_readiness_v3(
    runtime_full_state: Dict,
    consistency: Dict,
    cross_process: Dict,
    external_ood: Dict,
    multiseed: Dict,
    forbidden_scan: Dict,
    figure_data_pack_generated: bool,
    paper_figures_generated: bool,
) -> Dict:
    blockers: List[str] = []
    support_level = runtime_full_state.get("persisted_state_support_level", "unavailable")
    if support_level != "full_router_root":
        blockers.append(f"persisted_state_support_level is {support_level}, not full_router_root")
    if consistency.get("runtime_full_state_consistency_passed") is not True:
        blockers.append("runtime full state consistency failed")
    if cross_process.get("cross_process_reload_passed") is not True:
        blockers.append("cross-process reload failed")
    if external_ood.get("overall_ood_false_accept_rate", 1.0) > 0.10:
        blockers.append("external OOD false accept above threshold")
    supported_retention = cross_process.get("current_supported_retention_rate", external_ood.get("current_supported_retention_rate", 1.0))
    if supported_retention < 0.98:
        blockers.append("supported retention below threshold")
    if multiseed.get("stable_across_seeds") is not True:
        blockers.append("multi-seed stability not established")
    if forbidden_scan.get("forbidden_field_in_state_count", 1) != 0:
        blockers.append("forbidden fields found in state")
    if not figure_data_pack_generated:
        blockers.append("paper figure data pack missing")
    if not paper_figures_generated:
        blockers.append("paper figures missing")
    ready = not blockers
    return {
        "ready_for_arxiv_technical_report": ready,
        "recommended_claim_level": "technical_report_candidate" if ready else "needs_more_validation",
        "blocking_issues": blockers,
        "recommended_title": "JianMu v0.9 Technical Report: Runtime State Capture and Boundary-Aware Routing",
        "recommended_abstract_boundary": "bounded no-label free-beam and persisted runtime-state evidence; not a stable convergence or solved OOD claim",
        "required_non_claims": [
            "stable convergence",
            "solved OOD",
            "solved arithmetic",
            "general program synthesis",
            "same-size LLM advantage",
            "safe real promotion",
        ],
        "suggested_next_experiments": ["external OOD expansion", "same-size baseline", "larger scale runtime ladder"],
    }
