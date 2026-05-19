from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LayerGateConfig:
    layer_name: str
    continue_threshold: int = 15
    min_margin: int = 0
    allow_typed_rejection: bool = True
    no_confidence_reason: str = "no_confident_branch_reject"


@dataclass
class ConfidenceGateResult:
    can_continue: bool
    selected_proposal: object
    reject_reason: Optional[str]
    reject_type: Optional[str]
    best_confidence: int
    second_best_confidence: int
    confidence_margin: int
    threshold: int


def apply_confidence_gate(layer_name: str, proposals: List, config: LayerGateConfig) -> ConfidenceGateResult:
    if not proposals:
        return ConfidenceGateResult(
            can_continue=False,
            selected_proposal=None,
            reject_reason=f"missing_layer:{layer_name}",
            reject_type="missing_layer",
            best_confidence=0,
            second_best_confidence=0,
            confidence_margin=0,
            threshold=config.continue_threshold,
        )

    ranked = sorted(proposals, key=lambda proposal: (proposal.confidence, proposal.selected, proposal.neuron_id), reverse=True)
    best = ranked[0]
    second = ranked[1].confidence if len(ranked) > 1 else 0
    margin = best.confidence - second

    if (best.selected.startswith("reject_") or best.selected == "unsupported") and config.allow_typed_rejection:
        best.can_continue = False
        best.reject_reason = best.selected
        best.confidence_margin = margin
        best.gate_threshold = config.continue_threshold
        return ConfidenceGateResult(
            can_continue=False,
            selected_proposal=best,
            reject_reason=best.selected,
            reject_type="typed_rejection",
            best_confidence=best.confidence,
            second_best_confidence=second,
            confidence_margin=margin,
            threshold=config.continue_threshold,
        )

    if best.confidence < config.continue_threshold or margin < config.min_margin:
        best.can_continue = False
        best.reject_reason = config.no_confidence_reason
        best.confidence_margin = margin
        best.gate_threshold = config.continue_threshold
        return ConfidenceGateResult(
            can_continue=False,
            selected_proposal=best,
            reject_reason=config.no_confidence_reason,
            reject_type="no_confident_branch",
            best_confidence=best.confidence,
            second_best_confidence=second,
            confidence_margin=margin,
            threshold=config.continue_threshold,
        )

    best.can_continue = True
    best.confidence_margin = margin
    best.gate_threshold = config.continue_threshold
    return ConfidenceGateResult(
        can_continue=True,
        selected_proposal=best,
        reject_reason=None,
        reject_type=None,
        best_confidence=best.confidence,
        second_best_confidence=second,
        confidence_margin=margin,
        threshold=config.continue_threshold,
    )

