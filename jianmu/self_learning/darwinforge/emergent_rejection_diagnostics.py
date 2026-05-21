from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class EmergentRejectionSignal:
    emergent_rejection_signal_score: float
    hard_ood_rejection_improvement: float
    trap_rejection_improvement: float
    supported_retention_delta: float
    future_domain_isolation_improvement: float
    near_ood_quarantine_delta: float
    toxic_false_accept_reduction: float
    rejection_layer_distribution_before: Dict
    rejection_layer_distribution_after: Dict
    support_gate_weight_shift: float | None
    task_scope_weight_shift: float | None
    language_target_weight_shift: float | None
    notes: str
    emergent_rejection_signal_confirmed: bool
    over_rejection_detected: bool
    rejection_boundary_improved: bool
    supported_retention_preserved: bool

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def diagnose_emergent_rejection(before: Dict, after: Dict, metadata: Dict | None = None) -> Dict:
    metadata = metadata or {}
    hard = after.get("hard_ood_rejection_rate", 0) - before.get("hard_ood_rejection_rate", 0)
    trap = after.get("true_false_accept_trap_rejection_rate", 0) - before.get("true_false_accept_trap_rejection_rate", 0)
    supported_delta = after.get("current_supported_retention_rate", 0) - before.get("current_supported_retention_rate", 0)
    future = after.get("future_domain_isolation_rate", 0) - before.get("future_domain_isolation_rate", 0)
    near = after.get("near_ood_quarantine_rate", 0) - before.get("near_ood_quarantine_rate", 0)
    toxic_reduction = before.get("overall_ood_false_accept_rate", 0) - after.get("overall_ood_false_accept_rate", 0)
    supported_preserved = supported_delta >= -0.02
    over_rejection = not supported_preserved
    improved = hard > 0 and trap > 0 and toxic_reduction > 0
    confirmed = bool(improved and supported_preserved and not metadata.get("hardcoded_rejection_rules_added") and not metadata.get("real_promotion_enabled") and metadata.get("metric_consistency_passed", True))
    score = round(max(hard, 0) + max(trap, 0) + max(future, 0) + max(near, 0) + max(toxic_reduction, 0) + min(supported_delta, 0.02), 6)
    signal = EmergentRejectionSignal(
        emergent_rejection_signal_score=score,
        hard_ood_rejection_improvement=round(hard, 6),
        trap_rejection_improvement=round(trap, 6),
        supported_retention_delta=round(supported_delta, 6),
        future_domain_isolation_improvement=round(future, 6),
        near_ood_quarantine_delta=round(near, 6),
        toxic_false_accept_reduction=round(toxic_reduction, 6),
        rejection_layer_distribution_before=metadata.get("rejection_layer_distribution_before", {}),
        rejection_layer_distribution_after=metadata.get("rejection_layer_distribution_after", {}),
        support_gate_weight_shift=metadata.get("support_gate_weight_shift"),
        task_scope_weight_shift=metadata.get("task_scope_weight_shift"),
        language_target_weight_shift=metadata.get("language_target_weight_shift"),
        notes="confirmed under probe criteria" if confirmed else "not confirmed under probe criteria",
        emergent_rejection_signal_confirmed=confirmed,
        over_rejection_detected=over_rejection,
        rejection_boundary_improved=improved,
        supported_retention_preserved=supported_preserved,
    )
    return signal.to_dict()
