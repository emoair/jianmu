from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.branchchain.branch_types import BranchPath
from jianmu.self_learning.branchchain.confidence_gate import LayerGateConfig, apply_confidence_gate
from jianmu.self_learning.darwinforge.candidate import CandidateGenome


@dataclass
class WideBeamBacktrackingConfig:
    beam_size: int = 32
    proposals_per_layer: int = 8
    exploration_quota: int = 2
    stochastic_samples_per_layer: int = 4
    confidence_noise: float = 3.0
    max_complete_paths: int = 128
    clone_count_per_layer: int = 4
    perturbation_scale: float = 0.15
    backtracking_window: int = 1
    backtracking_patience: int = 4
    max_backtracking_attempts: int = 3
    seed: int = 42
    canonicalization_enabled: bool = True


class WideBeamBacktrackingSearch:
    """Wide-Beam Backtracking Search（宽束回溯搜索） candidate generation."""

    def __init__(self, config: WideBeamBacktrackingConfig):
        self.config = config

    def generate_paths(self, population, features: Dict, active_clones: Optional[Dict[str, List]] = None, generation: int = 0) -> List[CandidateGenome]:
        rng = random.Random(self.config.seed + generation)
        active_clones = active_clones or {}
        partials = [([], 0.0, False, None, None)]
        for layer_name, options in LAYER_DEFINITIONS:
            expanded = []
            for decisions, cumulative, stopped, reason, reject_type in partials:
                if stopped:
                    expanded.append((decisions, cumulative, stopped, reason, reject_type))
                    continue
                proposals = self._layer_proposals(population, active_clones, layer_name, options, features, decisions, rng)
                gate = apply_confidence_gate(layer_name, [p for _, p in proposals], _gate_config(layer_name))
                if not proposals or not gate.can_continue:
                    selected = gate.selected_proposal
                    next_decisions = decisions + ([selected] if selected else [])
                    if selected:
                        selected.can_continue = False
                        selected.reject_reason = gate.reject_reason
                        selected.confidence_margin = gate.confidence_margin
                        selected.gate_threshold = gate.threshold
                    expanded.append((next_decisions, cumulative + gate.best_confidence, True, gate.reject_reason, gate.reject_type))
                    continue
                chosen = self._select_layer_expansions(proposals, rng)
                for adjusted_score, proposal in chosen:
                    proposal.can_continue = True
                    expanded.append((decisions + [proposal], cumulative + adjusted_score, False, None, None))
            partials = self._trim_partials(expanded)
        return self._to_genomes(partials, generation)[: self.config.max_complete_paths]

    def _layer_proposals(self, population, active_clones, layer_name, options, features, decisions, rng):
        proposals = []
        sources = [(None, population.per_layer.get(layer_name, []))]
        sources.extend((clone.clone_id, clone.neurons) for clone in active_clones.get(layer_name, []))
        for clone_id, neurons in sources:
            for neuron in neurons:
                proposal = neuron.propose(features, decisions)
                if not proposal or proposal.selected not in options:
                    continue
                proposal.candidates = list(options)
                proposal.evidence = dict(proposal.evidence)
                proposal.evidence["source_clone_id"] = clone_id or "base"
                raw_score = proposal.confidence + int(max(min(neuron.score_value, 20), -20))
                adjusted = raw_score + rng.uniform(-self.config.confidence_noise, self.config.confidence_noise)
                proposal.evidence["raw_score"] = raw_score
                proposal.evidence["adjusted_score"] = round(adjusted, 4)
                proposals.append((adjusted, proposal))
        proposals.sort(key=lambda item: (item[0], item[1].selected, item[1].neuron_id), reverse=True)
        return proposals

    def _select_layer_expansions(self, proposals, rng):
        selected = list(proposals[: self.config.proposals_per_layer])
        tail = proposals[self.config.proposals_per_layer :]
        if tail and self.config.exploration_quota:
            selected.extend(rng.sample(tail, min(self.config.exploration_quota, len(tail))))
        if proposals and self.config.stochastic_samples_per_layer:
            selected.extend(rng.choice(proposals) for _ in range(min(self.config.stochastic_samples_per_layer, len(proposals))))
        dedup = {}
        for score, proposal in selected:
            key = (proposal.layer_name, proposal.selected, proposal.neuron_id, proposal.evidence.get("source_clone_id"))
            dedup[key] = max(dedup.get(key, (score, proposal)), (score, proposal), key=lambda item: item[0])
        return sorted(dedup.values(), key=lambda item: item[0], reverse=True)

    def _trim_partials(self, partials):
        early = [item for item in partials if item[2]]
        continuing = [item for item in partials if not item[2]]
        continuing = sorted(continuing, key=lambda item: item[1], reverse=True)[: self.config.beam_size]
        early_quota = max(1, self.config.beam_size // 4)
        early = sorted(early, key=lambda item: item[1], reverse=True)[:early_quota]
        combined = sorted(continuing + early, key=lambda item: item[1], reverse=True)
        return combined[: self.config.beam_size]

    def _to_genomes(self, partials, generation):
        genomes = []
        for index, (decisions, cumulative, early_exit, reason, reject_type) in enumerate(sorted(partials, key=lambda item: item[1], reverse=True)):
            path = BranchPath(
                decisions=decisions,
                route_confidence=int(sum(d.confidence for d in decisions) / max(len(decisions), 1)),
                atomic_experts=[] if early_exit else ["ArithmeticExpressionExpert", "TargetIRBuilderExpert", "ConsistencyCheckExpert"],
                target_builder=decisions[-1].selected if decisions else "early_exit",
                early_exit=early_exit,
                unsupported_reason=reason,
                rejected_by_layer=_rejected_layer(decisions, reason) if early_exit else None,
                reject_reason=reason,
                reject_type=reject_type,
            )
            by_layer = {decision.layer_name: decision.selected for decision in decisions}
            genomes.append(
                CandidateGenome(
                    genome_id=f"wb{generation}:{index}:{abs(hash(tuple((d.layer_name, d.selected, d.evidence.get('source_clone_id')) for d in decisions))) % 10**8}",
                    branch_path=path,
                    atomic_expert_plan=path.atomic_experts,
                    slot_binding_policy=by_layer.get("slot_binding_policy", "unsupported"),
                    target_builder_policy=by_layer.get("target_builder", "early_exit"),
                    generation=generation,
                )
            )
        return genomes


def _gate_config(layer_name: str):
    defaults = {"task_scope": 5, "language_target": 5, "semantic_domain": 5, "support_gate": 5, "arithmetic_family": 5, "structure_policy": 5, "slot_binding_policy": 5, "target_builder": 5}
    return LayerGateConfig(layer_name=layer_name, continue_threshold=defaults.get(layer_name, 5), min_margin=0)


def _rejected_layer(decisions, reason):
    if reason and reason.startswith("missing_layer:"):
        return reason.split(":", 1)[1]
    return decisions[-1].layer_name if decisions else None

