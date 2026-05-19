from dataclasses import dataclass
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_neuron import BranchNeuron
from jianmu.self_learning.branchchain.branch_types import BranchPath


LAYER_DEFINITIONS = [
    ("task_scope", ["programming", "non_programming", "unsupported"]),
    ("language_target", ["C", "unknown"]),
    ("semantic_domain", ["arithmetic", "comparison_future", "unsupported"]),
    ("support_gate", ["supported", "unsupported"]),
    ("arithmetic_family", ["addition", "subtraction", "multiplication", "exact_division", "mixed_precedence", "parentheses", "unsupported"]),
    ("structure_policy", ["binary_operation", "reduce_chain", "precedence_tree", "parenthesized_tree", "unsupported"]),
    ("slot_binding_policy", ["surface_number_order", "chinese_number_order", "signed_number_order", "previous_targetir_delta", "unsupported"]),
    ("target_builder", ["canonical_arithmetic_targetir", "canonical_program_targetir", "early_exit"]),
]


@dataclass
class BranchChainRouter:
    population: List[BranchNeuron]
    layer_definitions: List = None
    top_k: int = 1
    layer_threshold: int = 1

    def __post_init__(self):
        if self.layer_definitions is None:
            self.layer_definitions = LAYER_DEFINITIONS

    def route(self, features: Dict) -> BranchPath:
        decisions = []
        for layer_name, candidates in self.layer_definitions:
            proposals = []
            for neuron in self.population:
                if neuron.layer_name != layer_name or neuron.option not in candidates:
                    continue
                proposal = neuron.propose(features, decisions)
                if proposal:
                    proposal.candidates = list(candidates)
                    proposals.append(proposal)
            if not proposals:
                return self._early_exit(decisions, "no_proposal")
            neuron_by_id = {neuron.neuron_id: neuron for neuron in self.population}
            best = max(
                proposals,
                key=lambda item: (
                    item.confidence + int(max(min(neuron_by_id[item.neuron_id].score_value, 20), -20)),
                    item.confidence,
                    item.selected,
                    item.neuron_id,
                ),
            )
            if best.confidence < self.layer_threshold:
                return self._early_exit(decisions, "low_confidence")
            decisions.append(best)
            if best.selected in {"unsupported", "early_exit"}:
                return self._early_exit(decisions, f"{layer_name}:{best.selected}")

        confidence = int(sum(decision.confidence for decision in decisions) / max(len(decisions), 1))
        return BranchPath(
            decisions=decisions,
            route_confidence=confidence,
            atomic_experts=["ArithmeticExpressionExpert", "TargetIRBuilderExpert", "ConsistencyCheckExpert"],
            target_builder=decisions[-1].selected if decisions else "",
            early_exit=False,
            unsupported_reason=None,
        )

    def candidate_paths(self, features: Dict) -> List[BranchPath]:
        return [self.route(features)]

    def _early_exit(self, decisions, reason: str) -> BranchPath:
        confidence = int(sum(decision.confidence for decision in decisions) / max(len(decisions), 1))
        return BranchPath(
            decisions=decisions,
            route_confidence=confidence,
            atomic_experts=[],
            target_builder="early_exit",
            early_exit=True,
            unsupported_reason=reason,
        )


def decision_pairs(path: BranchPath) -> List[List[str]]:
    return [[decision.layer_name, decision.selected] for decision in path.decisions]
