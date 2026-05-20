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
        "input_mode_guess_zh_natural",
        "input_mode_guess_math_expression",
        "input_mode_guess_zh_technical_mixed",
        "contains_chinese_chars",
        "is_pure_math_expression",
        "has_c_token",
        "has_printf_token",
        "has_main_token",
        "has_technical_token",
        "canonical_changed",
        "contains_canonicalized_zh_number",
        "unary_negative_only",
        "signed_literal_only",
        "binary_minus_present",
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
            "contains_arithmetic_operator": 18 if option == "programming" else -5,
            "is_pure_math_expression": 18 if option == "programming" else -5,
            "number_count": 12 if option == "programming" else -4,
            "canonical_changed": 14 if option == "programming" else -4,
            "contains_canonicalized_zh_number": 14 if option == "programming" else -4,
            "unrelated_keyword_signal": 30 if option in {"non_programming", "reject_non_programming"} else -12,
            "dangerous_keyword_signal": 35 if option == "reject_out_of_scope" else -10,
            "has_english_sentence": 30 if option == "unsupported" else -10,
        }
    if layer_name == "language_target":
        return {
            "contains_C": 25 if option in {"C", "explicit_C"} else -5,
            "contains_printf": 22 if option in {"C", "explicit_C"} else -5,
            "has_main_token": 18 if option in {"C", "explicit_C"} else -5,
            "input_mode_guess_zh_technical_mixed": 25 if option == "explicit_C" else -5,
            "input_mode_guess_zh_natural": 25 if option == "implicit_C" else -5,
            "input_mode_guess_math_expression": 30 if option == "math_expression_context" else -5,
            "number_count": 8 if option in {"implicit_C", "math_expression_context"} else -2,
            "canonical_changed": 14 if option in {"implicit_C", "math_expression_context"} else -3,
            "contains_canonicalized_zh_number": 16 if option in {"implicit_C", "math_expression_context"} else -4,
            "has_english_sentence": 35 if option == "reject_unsupported_language" else -12,
            "contains_chinese_chars": 12 if option in {"implicit_C", "explicit_C"} else -4,
        }
    if layer_name == "semantic_domain":
        return {
            "contains_arithmetic_operator": 25 if option == "arithmetic" else -8,
            "number_count": 12 if option == "arithmetic" else -4,
            "signed_literal_only": 20 if option == "arithmetic" else -8,
            "unrelated_keyword_signal": 25 if option == "unsupported" else -8,
        }
    if layer_name == "support_gate":
        return {
            "has_english_sentence": 40 if option == "unsupported" else -20,
            "unrelated_keyword_signal": 40 if option == "unsupported" else -20,
            "contains_arithmetic_operator": 20 if option == "supported" else -8,
            "number_count": 10 if option == "supported" else -4,
            "signed_literal_only": 16 if option == "supported" else -8,
        }
    if layer_name == "arithmetic_family":
        if option == "literal_only":
            return {
                "signed_literal_only": 45,
                "unary_negative_only": 45,
                "number_count": 28,
                "operator_count": -35,
                "is_pure_math_expression": 12,
                "canonical_changed": 10,
                "contains_output": 8,
            }
        return {
            "signed_literal_only": -18,
            "unary_negative_only": -18,
            "contains_plus": 25 if option == "addition" else -3,
            "contains_minus": 20 if option == "subtraction" else -3,
            "binary_minus_present": 35 if option == "subtraction" else -5,
            "contains_mul": 25 if option == "multiplication" else -3,
            "contains_div": 25 if option == "exact_division" else -3,
            "contains_parentheses": 35 if option == "parentheses" else -3,
            "operator_count": 12 if option == "mixed_precedence" else 0,
        }
    if layer_name == "structure_policy":
        if option == "literal_value":
            return {
                "signed_literal_only": 45,
                "unary_negative_only": 45,
                "number_count": 26,
                "operator_count": -30,
            }
        return {
            "operator_count": 20 if option == "binary_operation" else 0,
            "signed_literal_only": -20 if option in {"binary_operation", "precedence_tree", "parenthesized_tree"} else 0,
            "contains_parentheses": 35 if option == "parenthesized_tree" else -5,
        }
    if layer_name == "slot_binding_policy":
        return {
            "has_chinese_number": 30 if option == "chinese_number_order" else 0,
            "has_negative": 30 if option == "signed_number_order" else 0,
            "number_count": 10 if option == "surface_number_order" else 0,
        }
    if layer_name == "target_builder":
        return {
            "contains_arithmetic_operator": 20 if option == "canonical_arithmetic_targetir" else -5,
            "number_count": 18 if option == "canonical_arithmetic_targetir" else -5,
            "signed_literal_only": 24 if option == "canonical_arithmetic_targetir" else -8,
            "prev:semantic_domain=arithmetic": 18 if option == "canonical_arithmetic_targetir" else -6,
            "prev:support_gate=supported": 10 if option == "canonical_arithmetic_targetir" else -4,
        }
    return {}
