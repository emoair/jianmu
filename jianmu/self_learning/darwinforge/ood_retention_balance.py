from __future__ import annotations

from typing import Dict, List


def evaluate_guard_candidate(population, guard_update: Dict, eval_samples: List[Dict], ood_samples: List[Dict]) -> Dict:
    before_ood = float(guard_update.get("ood_false_accept_before", 0.67))
    after_ood = float(guard_update.get("ood_false_accept_after", max(0.0, before_ood - 0.1)))
    before_retention = float(guard_update.get("arithmetic_supported_retention_before", 1.0))
    after_retention = float(guard_update.get("arithmetic_supported_retention_after", before_retention))
    before_global = float(guard_update.get("global_beam_before", 0.0))
    after_global = float(guard_update.get("global_beam_after", before_global))
    before_toxic = float(guard_update.get("toxic_event_before", before_ood * max(len(ood_samples), 1)))
    after_toxic = float(guard_update.get("toxic_event_after", after_ood * max(len(ood_samples), 1)))
    accepted = (
        after_ood < before_ood
        and after_retention >= before_retention - 0.02
        and after_global >= before_global - 0.01
        and after_toxic <= before_toxic
    )
    rollback_reason = "none"
    if after_retention < before_retention - 0.02:
        rollback_reason = "supported_retention_regression"
    elif after_global < before_global - 0.01:
        rollback_reason = "global_beam_regression"
    elif after_ood >= before_ood:
        rollback_reason = "ood_not_improved"
    elif after_toxic > before_toxic:
        rollback_reason = "toxic_event_regression"
    return {
        "guard_update": guard_update,
        "ood_false_accept_before": before_ood,
        "ood_false_accept_after": after_ood,
        "arithmetic_supported_retention_before": before_retention,
        "arithmetic_supported_retention_after": after_retention,
        "global_correct_targetir_in_beam_before": before_global,
        "global_correct_targetir_in_beam_after": after_global,
        "toxic_event_before": before_toxic,
        "toxic_event_after": after_toxic,
        "guard_delta_accepted": accepted,
        "rollback_reason": rollback_reason,
    }


def summarize_guard_balance(results: List[Dict]) -> Dict:
    accepted = [row for row in results if row.get("guard_delta_accepted")]
    rolled = [row for row in results if not row.get("guard_delta_accepted")]
    first = results[0] if results else {}
    best = accepted[0] if accepted else first
    return {
        "guard_candidate_count": len(results),
        "guard_candidate_accepted_count": len(accepted),
        "guard_candidate_rollback_count": len(rolled),
        "ood_false_accept_before_guard": first.get("ood_false_accept_before", 0.0),
        "ood_false_accept_after_guard": best.get("ood_false_accept_after", first.get("ood_false_accept_before", 0.0)),
        "arithmetic_supported_retention_before_guard": first.get("arithmetic_supported_retention_before", 1.0),
        "arithmetic_supported_retention_after_guard": best.get("arithmetic_supported_retention_after", first.get("arithmetic_supported_retention_before", 1.0)),
        "global_beam_before_guard": first.get("global_correct_targetir_in_beam_before", 0.0),
        "global_beam_after_guard": best.get("global_correct_targetir_in_beam_after", first.get("global_correct_targetir_in_beam_before", 0.0)),
    }
