from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidateRecord
from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.fitness import compute_fitness


@dataclass
class SubBeamConfig:
    subbeam_size: int = 24
    proposals_per_layer: int = 6
    exploration_quota: int = 2
    stochastic_samples_per_layer: int = 3
    confidence_noise: float = 3.0
    perturbation_scale: float = 0.15
    max_complete_paths: int = 96
    seed: int = 42


@dataclass
class SubBeamRegrowthRequest:
    sample_id: str
    raw_text: str
    canonical_text: str
    stable_prefix: List[List[str]]
    fork_layer: str
    fork_reason: str
    target_option_at_fork: Optional[str]
    target_option_rank: Optional[int]
    score_gap: float
    teacher_guided: bool = False

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


@dataclass
class SubBeamRegrowthResult:
    sample_id: str
    fork_layer: str
    fork_reason: str
    path_count: int
    complete_path_count: int
    correct_targetir_in_subbeam: bool
    correct_path_in_subbeam: bool
    subbeam_best_targetir: Optional[str]
    subbeam_best_exact: bool
    rescued_from_global_failure: bool
    first_success_rank: Optional[int]
    generated_paths_summary: List[Dict] = field(default_factory=list)
    teacher_guided: bool = False
    diagnostic_bonus_applied: bool = False

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def run_prefix_conditioned_subbeam(population, sample: Dict, request: SubBeamRegrowthRequest, config: SubBeamConfig) -> SubBeamRegrowthResult:
    """Run Prefix-Conditioned Sub-Beam（前缀条件子束） regrowth.

    Teacher mode may add a diagnostic bonus to the target option at the fork,
    but free mode never forces or reads the current sample's target branch path.
    """

    rng = random.Random(config.seed + abs(hash((request.sample_id, request.fork_layer))) % 100000)
    features = build_training_features(sample["input_text"], canonicalization_enabled=True)
    prefix_decisions = _prefix_decisions(request.stable_prefix)
    start_index = _start_layer_index(request.fork_layer, request.stable_prefix)
    partials = [(prefix_decisions, 0.0)]
    diagnostic_bonus_applied = False
    for layer_name, options in LAYER_DEFINITIONS[start_index:]:
        expanded = []
        for decisions, cumulative in partials:
            proposals = _layer_proposals(population, features, decisions, layer_name, options, rng, config)
            if request.teacher_guided and layer_name == request.fork_layer and request.target_option_at_fork:
                proposals, applied = _apply_teacher_bonus(proposals, request.target_option_at_fork)
                diagnostic_bonus_applied = diagnostic_bonus_applied or applied
            chosen = _select(proposals, config, rng)
            for score, proposal in chosen:
                expanded.append((decisions + [proposal], cumulative + score))
        partials = sorted(expanded, key=lambda item: item[1], reverse=True)[: config.subbeam_size]
        if not partials:
            break
    genomes = _to_genomes(partials[: config.max_complete_paths], request)
    synthesis = AtomicSynthesis()
    records = []
    for genome in genomes:
        phenotype = synthesis.synthesize(genome, features)
        fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
        records.append(CandidateRecord(genome, phenotype, fitness))
    ranked = sorted(records, key=lambda record: record.fitness_report.total_fitness, reverse=True)
    exact_records = [record for record in ranked if sample.get("supported") and record.phenotype.target_ir_canonical == sample.get("target_ir_canonical")]
    path_records = [record for record in ranked if _path_matches(record.genome.branch_path.decisions, sample.get("target_branch_path", []))]
    first_success_rank = ranked.index(exact_records[0]) + 1 if exact_records else None
    top = ranked[0] if ranked else None
    return SubBeamRegrowthResult(
        sample_id=request.sample_id,
        fork_layer=request.fork_layer,
        fork_reason=request.fork_reason,
        path_count=len(ranked),
        complete_path_count=sum(1 for record in ranked if not record.genome.branch_path.early_exit),
        correct_targetir_in_subbeam=bool(exact_records),
        correct_path_in_subbeam=bool(path_records),
        subbeam_best_targetir=exact_records[0].phenotype.target_ir_canonical if exact_records else (top.phenotype.target_ir_canonical if top else None),
        subbeam_best_exact=bool(exact_records),
        rescued_from_global_failure=bool(exact_records),
        first_success_rank=first_success_rank,
        generated_paths_summary=[
            {
                "rank": index,
                "target_ir_pred": record.phenotype.target_ir_canonical,
                "fitness": record.fitness_report.total_fitness,
                "decisions": [[decision.layer_name, decision.selected] for decision in record.genome.branch_path.decisions],
            }
            for index, record in enumerate(ranked[:10], start=1)
        ],
        teacher_guided=request.teacher_guided,
        diagnostic_bonus_applied=diagnostic_bonus_applied,
    )


def summarize_subbeam_results(results: List[SubBeamRegrowthResult], global_failed_count: Optional[int] = None) -> Dict:
    count = len(results)
    rescued = sum(1 for result in results if result.rescued_from_global_failure)
    denominator = global_failed_count if global_failed_count is not None else count
    return {
        "subbeam_result_count": count,
        "correct_targetir_in_subbeam_rate": _rate(count, sum(1 for result in results if result.correct_targetir_in_subbeam)),
        "subbeam_rescue_rate": _rate(denominator, rescued),
        "rescued_sample_count": rescued,
    }


def _prefix_decisions(stable_prefix: List[List[str]]) -> List[BranchDecision]:
    option_by_layer = {layer: options for layer, options in LAYER_DEFINITIONS}
    return [
        BranchDecision(
            layer_name=layer,
            candidates=list(option_by_layer.get(layer, [selected])),
            selected=selected,
            confidence=100,
            neuron_id=f"prefix:{layer}:{selected}",
            evidence={"prefix_conditioned_subbeam": True},
        )
        for layer, selected in stable_prefix
    ]


def _start_layer_index(fork_layer: str, stable_prefix: List[List[str]]) -> int:
    order = [layer for layer, _ in LAYER_DEFINITIONS]
    if fork_layer in order:
        return order.index(fork_layer)
    if stable_prefix:
        last = stable_prefix[-1][0]
        return min(order.index(last) + 1, len(order)) if last in order else 0
    return 0


def _layer_proposals(population, features, decisions, layer_name, options, rng, config):
    proposals = []
    for neuron in population.per_layer.get(layer_name, []):
        proposal = neuron.propose(features, decisions)
        if not proposal or proposal.selected not in options:
            continue
        proposal.candidates = list(options)
        proposal.evidence = dict(proposal.evidence)
        proposal.evidence["subbeam_source"] = "base"
        raw_score = proposal.confidence + int(max(min(neuron.score_value, 20), -20))
        adjusted = raw_score + rng.uniform(-config.confidence_noise, config.confidence_noise)
        proposal.evidence["raw_score"] = raw_score
        proposal.evidence["adjusted_score"] = round(adjusted, 4)
        proposals.append((adjusted, proposal))
    return sorted(proposals, key=lambda item: (item[0], item[1].selected, item[1].neuron_id), reverse=True)


def _apply_teacher_bonus(proposals, target_option):
    applied = False
    updated = []
    for score, proposal in proposals:
        if proposal.selected == target_option:
            proposal.evidence["teacher_diagnostic_bonus"] = 25.0
            score += 25.0
            applied = True
        updated.append((score, proposal))
    return sorted(updated, key=lambda item: item[0], reverse=True), applied


def _select(proposals, config, rng):
    selected = list(proposals[: config.proposals_per_layer])
    tail = proposals[config.proposals_per_layer :]
    if tail and config.exploration_quota:
        selected.extend(rng.sample(tail, min(config.exploration_quota, len(tail))))
    if proposals and config.stochastic_samples_per_layer:
        selected.extend(rng.choice(proposals) for _ in range(min(config.stochastic_samples_per_layer, len(proposals))))
    dedup = {}
    for score, proposal in selected:
        key = (proposal.layer_name, proposal.selected, proposal.neuron_id)
        if key not in dedup or score > dedup[key][0]:
            dedup[key] = (score, proposal)
    return sorted(dedup.values(), key=lambda item: item[0], reverse=True)


def _to_genomes(partials, request):
    genomes = []
    for index, (decisions, cumulative) in enumerate(sorted(partials, key=lambda item: item[1], reverse=True)):
        path = BranchPath(
            decisions=decisions,
            route_confidence=int(sum(d.confidence for d in decisions) / max(len(decisions), 1)),
            atomic_experts=["ArithmeticExpressionExpert", "TargetIRBuilderExpert", "ConsistencyCheckExpert"],
            target_builder=decisions[-1].selected if decisions else "early_exit",
            early_exit=False,
        )
        by_layer = {decision.layer_name: decision.selected for decision in decisions}
        genomes.append(
            CandidateGenome(
                genome_id=f"subbeam:{request.sample_id}:{index}",
                branch_path=path,
                atomic_expert_plan=path.atomic_experts,
                slot_binding_policy=by_layer.get("slot_binding_policy", "unsupported"),
                target_builder_policy=by_layer.get("target_builder", "early_exit"),
            )
        )
    return genomes


def _path_matches(decisions, target_path):
    candidate_pairs = [(decision.layer_name, decision.selected) for decision in decisions]
    target_pairs = [tuple(item) for item in target_path]
    target_layers = {layer for layer, _ in target_pairs}
    if "support_gate" not in target_layers:
        candidate_pairs = [(layer, selected) for layer, selected in candidate_pairs if not (layer == "support_gate" and selected == "supported")]
    return bool(target_pairs and candidate_pairs[: len(target_pairs)] == target_pairs)


def _rate(denominator, numerator):
    if not denominator:
        return 0.0
    return round(numerator / denominator, 4)
