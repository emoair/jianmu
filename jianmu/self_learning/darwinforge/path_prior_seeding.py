from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List


ALLOWED_FEATURE_CONDITIONS = {
    "signed_literal_only",
    "number_count",
    "operator_count",
    "contains_plus",
    "contains_div",
    "contains_parentheses",
    "input_mode_guess_math_expression",
    "canonical_changed",
    "input_mode",
    "expression_family",
    "structure_policy",
}


@dataclass
class PathPriorSeed:
    seed_id: str
    layer_name: str
    option: str
    feature_conditions: Dict
    weight_updates: Dict[str, int]
    source_sample_count: int
    confidence: float = 1.0
    seed_type: str = "path_prior"

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def build_path_prior_seeds(samples: List[Dict], path_forcing_records: List[Dict], score_diagnostics: List[Dict]) -> List[PathPriorSeed]:
    """Build Path-Prior Seeding（路径先验播种） records from training diagnostics."""

    train_samples = {sample.get("sample_id"): sample for sample in samples if sample.get("split", "train") == "train"}
    forcing_ok = {row.get("sample_id") for row in path_forcing_records if row.get("exact_match")}
    grouped = defaultdict(lambda: {"count": 0, "updates": Counter(), "conditions": Counter()})
    for diag_row in score_diagnostics:
        sample_id = diag_row.get("sample_id")
        if sample_id not in train_samples or sample_id not in forcing_ok:
            continue
        sample = train_samples[sample_id]
        for layer_row in diag_row.get("score_diagnostic", {}).get("layers", []):
            layer_name = layer_row["layer_name"]
            option = layer_row["target_option"]
            key = (layer_name, option, _seed_family(layer_name, option, sample))
            grouped[key]["count"] += 1
            for name, value in _feature_conditions(sample).items():
                if name in ALLOWED_FEATURE_CONDITIONS and value not in (None, False, "", 0):
                    grouped[key]["conditions"][(name, value)] += 1
            grouped[key]["updates"].update(_weight_updates_for(layer_name, option, sample))
    seeds = []
    for index, ((layer_name, option, seed_family), payload) in enumerate(sorted(grouped.items())):
        if payload["count"] <= 0:
            continue
        conditions = _top_conditions(payload["conditions"])
        updates = {name: max(min(value, 8), -8) for name, value in payload["updates"].items()}
        seeds.append(
            PathPriorSeed(
                seed_id=f"pps:{index}:{layer_name}:{option}:{seed_family}",
                layer_name=layer_name,
                option=option,
                feature_conditions=conditions,
                weight_updates=updates,
                source_sample_count=payload["count"],
                confidence=round(min(1.0, 0.35 + payload["count"] / 20), 4),
                seed_type=seed_family,
            )
        )
    return seeds


def apply_path_prior_seeds(population, seeds: Iterable[PathPriorSeed]) -> Dict:
    seeds = list(seeds)
    updated = 0
    layer_counter = Counter()
    literal = 0
    precedence = 0
    ood_guard = 0
    for seed in seeds:
        matched = [neuron for neuron in population.per_layer.get(seed.layer_name, []) if neuron.option == seed.option]
        for neuron in matched:
            for name, delta in seed.weight_updates.items():
                neuron.weights[name] = neuron.weights.get(name, 0) + delta
            neuron.score_value += seed.confidence
            updated += 1
        if matched:
            layer_counter[seed.layer_name] += 1
            literal += int(seed.seed_type == "literal_only")
            precedence += int(seed.seed_type in {"precedence_tree", "parenthesized_tree"})
            ood_guard += int(seed.seed_type == "ood_guard")
    return {
        "path_prior_seed_count": len(seeds),
        "branch_neuron_updated_count": updated,
        "layer_seed_distribution": dict(layer_counter),
        "literal_only_seed_count": literal,
        "precedence_seed_count": precedence,
        "ood_guard_seed_count": ood_guard,
    }


def _feature_conditions(sample: Dict) -> Dict:
    return {
        "input_mode": sample.get("input_mode"),
        "expression_family": sample.get("expression_family"),
        "structure_policy": sample.get("structure_policy"),
        "number_count": sample.get("number_count"),
        "operator_count": sample.get("operator_count"),
        "contains_parentheses": sample.get("has_parentheses"),
    }


def _weight_updates_for(layer_name: str, option: str, sample: Dict) -> Dict[str, int]:
    structure = sample.get("structure_policy")
    family = sample.get("expression_family")
    updates = {}
    if structure == "literal_value" or option == "literal_only":
        updates.update({"signed_literal_only": 5, "number_count": 2, "operator_count": -4})
    if structure == "precedence_tree" or family == "mixed_precedence":
        updates.update({"operator_count": 3, "contains_plus": 2, "contains_div": 2})
    if structure == "parenthesized_tree":
        updates.update({"contains_parentheses": 5, "operator_count": 2})
    if sample.get("input_mode") in {"math_expression", "arabic_math_expression", "zh_number_expression"}:
        updates["input_mode_guess_math_expression"] = 2
    if sample.get("input_mode") in {"zh_number_expression", "paired_zh_natural", "mixed_zh_arabic"}:
        updates["canonical_changed"] = 2
    if layer_name == "target_builder" and option == "canonical_arithmetic_targetir":
        updates["number_count"] = max(updates.get("number_count", 0), 3)
    return updates or {"number_count": 1}


def _seed_family(layer_name: str, option: str, sample: Dict) -> str:
    if sample.get("structure_policy") == "literal_value" or option == "literal_only":
        return "literal_only"
    if sample.get("structure_policy") in {"precedence_tree", "parenthesized_tree"}:
        return sample["structure_policy"]
    if option in {"unsupported", "reject_unsupported_language", "reject_non_programming", "reject_out_of_scope"}:
        return "ood_guard"
    return "path_prior"


def _top_conditions(counter: Counter) -> Dict:
    conditions = {}
    for (name, value), _ in counter.most_common(6):
        if name in ALLOWED_FEATURE_CONDITIONS:
            conditions[name] = value
    return conditions
