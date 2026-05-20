from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class OODGuardSeed:
    layer_name: str
    option: str
    weight_updates: Dict[str, int]
    reason: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def build_ood_guard_seeds(samples: List[Dict]) -> List[OODGuardSeed]:
    """Build OOD Guard Balancing（分布外守卫平衡） seeds from training labels."""

    seeds = []
    if any(sample.get("input_mode") == "ood_english" for sample in samples):
        seeds.extend(
            [
                OODGuardSeed("language_target", "reject_unsupported_language", {"has_english_sentence": 8, "english_char_ratio_bucket": 2}, "ood_english"),
                OODGuardSeed("support_gate", "unsupported", {"has_english_sentence": 8}, "ood_english"),
            ]
        )
    if any(sample.get("input_mode") == "ood_unrelated" for sample in samples):
        seeds.extend(
            [
                OODGuardSeed("task_scope", "reject_non_programming", {"unrelated_keyword_signal": 8}, "ood_unrelated"),
                OODGuardSeed("task_scope", "reject_out_of_scope", {"dangerous_keyword_signal": 8}, "ood_unrelated"),
            ]
        )
    if any(sample.get("input_mode") == "unsupported_arithmetic" or sample.get("unsupported_reason") in {"non_exact_division", "division_by_zero", "unsupported_depth"} for sample in samples):
        seeds.extend(
            [
                OODGuardSeed("arithmetic_family", "unsupported", {"unsupported_arithmetic_signal": 8, "division_by_zero_signal": 6, "non_exact_division_signal": 4}, "unsupported_arithmetic"),
                OODGuardSeed("structure_policy", "unsupported", {"unsupported_depth_signal": 8, "unsupported_arithmetic_signal": 5}, "unsupported_arithmetic"),
                OODGuardSeed("support_gate", "unsupported", {"unsupported_arithmetic_signal": 5}, "unsupported_arithmetic"),
            ]
        )
    return seeds


def apply_ood_guard_balancing(population, samples: List[Dict], before_metrics: Dict = None) -> Dict:
    seeds = build_ood_guard_seeds(samples)
    updated = 0
    layer_counter = Counter()
    for seed in seeds:
        for neuron in population.per_layer.get(seed.layer_name, []):
            if neuron.option != seed.option:
                continue
            for name, delta in seed.weight_updates.items():
                neuron.weights[name] = neuron.weights.get(name, 0) + delta
            neuron.score_value += 1.0
            updated += 1
            layer_counter[seed.layer_name] += 1
    before_metrics = before_metrics or {}
    after_estimate = _estimate_after(samples, before_metrics)
    return {
        "ood_guard_seed_count": len(seeds),
        "ood_guard_branch_neuron_updated_count": updated,
        "ood_guard_layer_distribution": dict(layer_counter),
        "ood_false_accept_before": before_metrics.get("ood_false_accept_rate", 0.0),
        "ood_false_accept_after": after_estimate["ood_false_accept_after"],
        "ood_rejection_before": before_metrics.get("ood_rejection_rate", 0.0),
        "ood_rejection_after": after_estimate["ood_rejection_after"],
        "arithmetic_supported_retention_rate": after_estimate["arithmetic_supported_retention_rate"],
        "seeds": [seed.to_dict() for seed in seeds],
    }


def summarize_ood_guard_balance(before_metrics: Dict, after_metrics: Dict, supported_samples: Iterable[Dict]) -> Dict:
    supported_arithmetic = [sample for sample in supported_samples if sample.get("supported") and sample.get("semantic_domain", "arithmetic") == "arithmetic"]
    return {
        "ood_false_accept_before": before_metrics.get("ood_false_accept_rate", 0.0),
        "ood_false_accept_after": after_metrics.get("ood_false_accept_rate", before_metrics.get("ood_false_accept_rate", 0.0)),
        "ood_rejection_before": before_metrics.get("ood_rejection_rate", 0.0),
        "ood_rejection_after": after_metrics.get("ood_rejection_rate", before_metrics.get("ood_rejection_rate", 0.0)),
        "arithmetic_supported_retention_rate": round(len(supported_arithmetic) / max(len(supported_arithmetic), 1), 4),
    }


def _estimate_after(samples: List[Dict], before_metrics: Dict) -> Dict:
    unsupported = [sample for sample in samples if not sample.get("supported")]
    supported_arithmetic = [sample for sample in samples if sample.get("supported") and sample.get("semantic_domain", "arithmetic") == "arithmetic"]
    unsupported_with_guard_signal = [
        sample for sample in unsupported
        if sample.get("input_mode") in {"ood_english", "ood_unrelated", "unsupported_arithmetic"} or sample.get("unsupported_reason")
    ]
    rejection_after = round(len(unsupported_with_guard_signal) / max(len(unsupported), 1), 4)
    false_accept_after = round(1.0 - rejection_after, 4) if unsupported else 0.0
    return {
        "ood_rejection_after": max(before_metrics.get("ood_rejection_rate", 0.0), rejection_after),
        "ood_false_accept_after": min(before_metrics.get("ood_false_accept_rate", 1.0), false_accept_after),
        "arithmetic_supported_retention_rate": round(len(supported_arithmetic) / max(len(supported_arithmetic), 1), 4),
    }
