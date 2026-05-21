from __future__ import annotations

from typing import Dict, Iterable, List


def compute_boundary_metrics(samples: List[Dict], candidate_results: List[Dict], reward_signals: List[Dict] | None = None) -> Dict:
    rows = list(zip(samples, candidate_results))
    reward_signals = reward_signals or []
    by_label = {}
    for label in [
        "current_supported",
        "hard_ood",
        "true_false_accept_trap",
        "future_domain_candidate",
        "near_ood_generalization_candidate",
    ]:
        by_label[label] = [(s, r) for s, r in rows if s.get("boundary_label") == label]
    current = by_label["current_supported"]
    hard = by_label["hard_ood"]
    trap = by_label["true_false_accept_trap"]
    future = by_label["future_domain_candidate"]
    near = by_label["near_ood_generalization_candidate"]
    ood = hard + trap + future + near
    return {
        "current_supported_retention_rate": _rate(current, lambda s, r: r.get("accepted_as_supported") and not r.get("rejected")),
        "current_supported_false_reject_rate": _rate(current, lambda s, r: r.get("rejected")),
        "hard_ood_rejection_rate": _rate(hard, lambda s, r: r.get("rejected")),
        "hard_ood_false_accept_rate": _rate(hard, lambda s, r: r.get("accepted_as_supported")),
        "true_false_accept_trap_rejection_rate": _rate(trap, lambda s, r: r.get("rejected")),
        "true_false_accept_trap_false_accept_rate": _rate(trap, lambda s, r: r.get("accepted_as_supported")),
        "future_domain_isolation_rate": _rate(future, lambda s, r: r.get("rejected") or r.get("future_buffered")),
        "future_domain_false_accept_rate": _rate(future, lambda s, r: r.get("accepted_as_supported")),
        "near_ood_quarantine_rate": _rate(near, lambda s, r: r.get("quarantined") or r.get("candidate_buffered")),
        "near_ood_false_supported_accept_rate": _rate(near, lambda s, r: r.get("accepted_as_supported") and not r.get("quarantined")),
        "overall_ood_false_accept_rate": _rate(ood, lambda s, r: r.get("accepted_as_supported")),
        "false_accept_toxicity_rate": _rate(list(zip(samples, reward_signals)), lambda s, sig: sig.get("toxicity_reason", "").endswith("false_accept") or "false_accept" in sig.get("toxicity_reason", "")),
        "false_reject_supported_toxicity_rate": _rate(list(zip(samples, reward_signals)), lambda s, sig: sig.get("toxicity_reason") == "current_supported_false_reject"),
        "boundary_reward_total": round(sum(sig.get("positive_reward", 0.0) for sig in reward_signals), 6),
        "boundary_toxicity_total": round(sum(sig.get("toxicity", 0.0) for sig in reward_signals), 6),
    }


def before_after_metrics(before: Dict, after: Dict) -> Dict:
    return {"before": before, "after": after, "delta": {key: round(after.get(key, 0) - before.get(key, 0), 6) for key in before if isinstance(before.get(key), (int, float))}}


def _rate(rows: Iterable, pred) -> float:
    rows = list(rows)
    if not rows:
        return 0.0
    return round(sum(1 for args in rows if pred(*args)) / len(rows), 6)
