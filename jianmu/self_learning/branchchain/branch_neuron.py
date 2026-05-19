import copy
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_types import BranchDecision
from jianmu.self_learning.branchchain.surface_features import numeric_feature_view


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


@dataclass
class BranchNeuron:
    neuron_id: str
    layer_name: str
    option: str
    weights: Dict[str, int] = field(default_factory=dict)
    threshold: int = 1
    score_value: float = 0.0
    mutation_count: int = 0

    def score(self, features: Dict, previous_decisions: List[BranchDecision]) -> int:
        numeric = numeric_feature_view(features)
        total = sum(self.weights.get(name, 0) * value for name, value in numeric.items())
        for decision in previous_decisions:
            total += self.weights.get(f"prev:{decision.layer_name}={decision.selected}", 0)
        return clamp(total)

    def propose(self, features: Dict, previous_decisions: List[BranchDecision]) -> Optional[BranchDecision]:
        confidence = self.score(features, previous_decisions)
        if confidence < self.threshold:
            return None
        evidence = {
            "threshold": self.threshold,
            "active_weight_count": sum(1 for value in self.weights.values() if value),
        }
        return BranchDecision(
            layer_name=self.layer_name,
            candidates=[self.option],
            selected=self.option,
            confidence=confidence,
            neuron_id=self.neuron_id,
            evidence=evidence,
        )

    def mutate(self, rng: random.Random):
        child = self.clone(f"{self.neuron_id}.m{self.mutation_count + 1}")
        keys = list(child.weights.keys()) or ["contains_output"]
        key = rng.choice(keys)
        child.weights[key] = child.weights.get(key, 0) + rng.choice([-1, 1])
        if rng.random() < 0.25:
            child.threshold = clamp(child.threshold + rng.choice([-1, 1]), 0, 100)
        child.mutation_count += 1
        child.score_value = 0.0
        return child

    def clone(self, new_id: str) -> "BranchNeuron":
        return BranchNeuron(
            neuron_id=new_id,
            layer_name=self.layer_name,
            option=self.option,
            weights=copy.deepcopy(self.weights),
            threshold=self.threshold,
            score_value=self.score_value,
            mutation_count=self.mutation_count,
        )


def make_seed_neurons(layer_name: str, options: List[str], start_index: int = 0) -> List[BranchNeuron]:
    neurons = []
    for offset, option in enumerate(options):
        weights = _default_weights(layer_name, option)
        neurons.append(
            BranchNeuron(
                neuron_id=f"{layer_name}:{option}:{start_index + offset}",
                layer_name=layer_name,
                option=option,
                weights=weights,
                threshold=1,
            )
        )
    return neurons


def make_random_neuron(layer_name: str, option: str, neuron_id: str, rng: random.Random) -> BranchNeuron:
    feature_names = [
        "contains_C",
        "contains_program",
        "contains_output",
        "contains_printf",
        "contains_arithmetic_operator",
        "contains_plus",
        "contains_minus",
        "contains_mul",
        "contains_div",
        "contains_parentheses",
        "number_count",
        "operator_count",
        "has_english_sentence",
        "unrelated_keyword_signal",
        "dangerous_keyword_signal",
        "has_chinese_number",
        "has_negative",
    ]
    weights = {rng.choice(feature_names): rng.randint(-2, 3) for _ in range(4)}
    return BranchNeuron(
        neuron_id=neuron_id,
        layer_name=layer_name,
        option=option,
        weights=weights,
        threshold=rng.randint(0, 8),
    )


def _default_weights(layer_name: str, option: str) -> Dict[str, int]:
    if layer_name == "task_scope":
        return {
            "contains_output": 20 if option == "programming" else -5,
            "contains_program": 12 if option == "programming" else -3,
            "contains_printf": 12 if option == "programming" else -3,
            "unrelated_keyword_signal": 30 if option == "non_programming" else -12,
            "has_english_sentence": 30 if option == "unsupported" else -10,
        }
    if layer_name == "language_target":
        return {"contains_C": 25 if option == "C" else -5, "contains_printf": 18 if option == "C" else -5}
    if layer_name == "semantic_domain":
        return {
            "contains_arithmetic_operator": 25 if option == "arithmetic" else -8,
            "unrelated_keyword_signal": 25 if option == "unsupported" else -8,
        }
    if layer_name == "support_gate":
        return {
            "has_english_sentence": 40 if option == "unsupported" else -20,
            "unrelated_keyword_signal": 40 if option == "unsupported" else -20,
            "contains_arithmetic_operator": 20 if option == "supported" else -8,
        }
    if layer_name == "arithmetic_family":
        return {
            "contains_plus": 25 if option == "addition" else -3,
            "contains_minus": 25 if option == "subtraction" else -3,
            "contains_mul": 25 if option == "multiplication" else -3,
            "contains_div": 25 if option == "exact_division" else -3,
            "contains_parentheses": 35 if option == "parentheses" else -3,
            "operator_count": 12 if option == "mixed_precedence" else 0,
        }
    if layer_name == "structure_policy":
        return {
            "operator_count": 20 if option == "binary_operation" else 0,
            "contains_parentheses": 35 if option == "parenthesized_tree" else -5,
        }
    if layer_name == "slot_binding_policy":
        return {
            "has_chinese_number": 30 if option == "chinese_number_order" else 0,
            "has_negative": 30 if option == "signed_number_order" else 0,
            "number_count": 10 if option == "surface_number_order" else 0,
        }
    if layer_name == "target_builder":
        return {"contains_arithmetic_operator": 20 if option == "canonical_arithmetic_targetir" else -5}
    return {}
