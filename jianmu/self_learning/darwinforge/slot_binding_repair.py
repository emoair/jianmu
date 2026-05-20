from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.router_score_diagnostics import score_target_branch_path, summarize_router_score_diagnostics


@dataclass
class SlotBindingRepairConfig:
    surface_bonus: int = 5
    signed_bonus: int = 7
    chinese_bonus: int = 3
    score_value_bonus: float = 1.0


def apply_slot_binding_repair(population, train_samples: List[Dict], before_score_rows: List[Dict], config: SlotBindingRepairConfig = None) -> Dict:
    """Apply Slot Binding Repair（槽位绑定修复） as train-only prior updates."""

    config = config or SlotBindingRepairConfig()
    before = summarize_slot_binding_scores(before_score_rows)
    updates = Counter()
    for sample in train_samples:
        if not sample.get("supported"):
            continue
        option = _target_slot_option(sample)
        for neuron in population.per_layer.get("slot_binding_policy", []):
            if neuron.option != option:
                continue
            if option == "surface_number_order":
                neuron.weights["number_count"] = neuron.weights.get("number_count", 0) + config.surface_bonus
                neuron.weights["operator_count"] = neuron.weights.get("operator_count", 0) + 1
                neuron.weights["input_mode_guess_math_expression"] = neuron.weights.get("input_mode_guess_math_expression", 0) + 2
            elif option == "signed_number_order":
                neuron.weights["has_negative"] = neuron.weights.get("has_negative", 0) + config.signed_bonus
                neuron.weights["signed_literal_only"] = neuron.weights.get("signed_literal_only", 0) + config.signed_bonus
                neuron.weights["binary_minus_present"] = neuron.weights.get("binary_minus_present", 0) + 2
            elif option == "chinese_number_order":
                neuron.weights["contains_canonicalized_zh_number"] = neuron.weights.get("contains_canonicalized_zh_number", 0) + config.chinese_bonus
                neuron.weights["canonical_changed"] = neuron.weights.get("canonical_changed", 0) + config.chinese_bonus
            neuron.score_value += config.score_value_bonus
            updates[option] += 1
    after_rows = _rescore_slot_binding(population, train_samples[: min(len(train_samples), 200)])
    after = summarize_slot_binding_scores(after_rows)
    return {
        "slot_binding_correct_rank_before": before["slot_binding_correct_rank"],
        "slot_binding_correct_rank_after": after["slot_binding_correct_rank"],
        "slot_binding_correct_score_before": before["slot_binding_correct_score"],
        "slot_binding_correct_score_after": after["slot_binding_correct_score"],
        "slot_binding_low_score_layer_count_before": before["slot_binding_low_score_layer_count"],
        "slot_binding_low_score_layer_count_after": after["slot_binding_low_score_layer_count"],
        "slot_binding_update_distribution": dict(updates),
    }


def summarize_slot_binding_scores(score_rows: List[Dict]) -> Dict:
    ranks = []
    scores = []
    low_count = 0
    for row in score_rows:
        diag = row.get("score_diagnostic", row)
        for layer_row in diag.get("layers", []):
            if layer_row.get("layer_name") != "slot_binding_policy":
                continue
            if layer_row.get("target_option_rank") is not None:
                ranks.append(layer_row["target_option_rank"])
            scores.append(layer_row.get("target_option_score", 0))
            if layer_row.get("target_option_rank", 99) > 3:
                low_count += 1
    return {
        "slot_binding_correct_rank": round(sum(ranks) / max(len(ranks), 1), 4),
        "slot_binding_correct_score": round(sum(scores) / max(len(scores), 1), 4),
        "slot_binding_low_score_layer_count": low_count,
    }


def _rescore_slot_binding(population, samples: List[Dict]) -> List[Dict]:
    rows = []
    for sample in samples:
        if not sample.get("supported"):
            continue
        features = build_training_features(sample["input_text"], canonicalization_enabled=True)
        diag = score_target_branch_path(population, features, sample.get("target_branch_path", []), proposals_per_layer=6)
        rows.append({"sample_id": sample.get("sample_id"), "score_diagnostic": diag})
    return rows


def _target_slot_option(sample: Dict) -> str:
    for layer, option in sample.get("target_branch_path", []):
        if layer == "slot_binding_policy":
            if option == "chinese_number_order":
                # Canonical Symbol Layer（规范符号层） already exposes canonical text; keep surface order viable.
                return "surface_number_order" if sample.get("input_mode") in {"zh_number_expression", "paired_zh_natural", "mixed_zh_arabic"} else option
            return option
    return "surface_number_order"
