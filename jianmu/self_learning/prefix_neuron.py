from dataclasses import dataclass
from typing import Optional

from jianmu.self_learning.ir_tokens import IRToken
from jianmu.self_learning.prefix_state import PrefixState


@dataclass(frozen=True)
class TokenProposal:
    neuron_id: str
    token: IRToken
    confidence: int
    rationale: str


@dataclass
class PrefixNeuron:
    neuron_id: str
    rule_type: str
    target_token_type: str
    target_value_policy: str = "none"
    weight: int = 10
    score: float = 0.0
    mutation_count: int = 0

    def propose(self, state: PrefixState) -> TokenProposal:
        token = IRToken(
            self.target_token_type,
            self._resolve_value(state),
        )
        applicable = _rule_applies(self.rule_type, state)
        confidence = self.weight + (70 if applicable else 0)
        confidence = max(0, min(100, confidence))
        return TokenProposal(
            neuron_id=self.neuron_id,
            token=token,
            confidence=confidence,
            rationale=f"{self.rule_type}:{self.target_token_type}:{self.target_value_policy}",
        )

    def clone(self, neuron_id: str) -> "PrefixNeuron":
        return PrefixNeuron(
            neuron_id=neuron_id,
            rule_type=self.rule_type,
            target_token_type=self.target_token_type,
            target_value_policy=self.target_value_policy,
            weight=self.weight,
            score=self.score,
            mutation_count=self.mutation_count,
        )

    def _resolve_value(self, state: PrefixState) -> Optional[int]:
        numbers = state.input_features.get("numbers", [])
        if self.target_value_policy == "first_number" and numbers:
            return numbers[0]
        if self.target_value_policy == "second_number" and len(numbers) >= 2:
            return numbers[1]
        if self.target_value_policy == "constant":
            return 1
        return None


def _rule_applies(rule_type: str, state: PrefixState) -> bool:
    features = state.prefix_features
    length = features["prefix_length"]
    literal_count = features["literal_count"]
    if rule_type == "start_include":
        return length == 0
    if rule_type == "after_include_main":
        return features["last_token_type"] == "INCLUDE_STDIO"
    if rule_type == "emit_first_literal":
        return features["has_main_begin"] and literal_count == 0
    if rule_type == "emit_second_literal":
        return literal_count == 1
    if rule_type == "emit_add_after_two_literals":
        return literal_count == 2 and not features["has_add"]
    if rule_type == "emit_print_after_add":
        return features["has_add"] and not features["has_print"]
    if rule_type == "emit_end_after_print":
        return features["has_print"] and not features["is_complete"]
    if rule_type == "random_token":
        return True
    return False

