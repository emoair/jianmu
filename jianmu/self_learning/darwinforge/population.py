import random
from collections import defaultdict
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.branchchain.branch_neuron import BranchNeuron, make_random_neuron, make_seed_neurons
from jianmu.self_learning.branchchain.branch_types import BranchPath
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidateRecord


class LayerPreservedPopulation:
    def __init__(self, per_layer: Dict[str, List[BranchNeuron]], seed: int = 42, generation: int = 0):
        self.per_layer = per_layer
        self.seed = seed
        self.generation = generation
        self.rng = random.Random(seed)

    @classmethod
    def initialize(cls, layer_definitions=None, population_per_layer: int = 16, seed: int = 42):
        layer_definitions = layer_definitions or LAYER_DEFINITIONS
        rng = random.Random(seed)
        per_layer: Dict[str, List[BranchNeuron]] = {}
        for layer_name, options in layer_definitions:
            neurons = []
            neurons.extend(make_seed_neurons(layer_name, options, 0))
            while len(neurons) < population_per_layer:
                option = rng.choice(options)
                neurons.append(make_random_neuron(layer_name, option, f"{layer_name}:immigrant:{len(neurons)}", rng))
            per_layer[layer_name] = neurons[:population_per_layer]
        return cls(per_layer=per_layer, seed=seed)

    def candidate_paths(self, features: Dict, top_k: int = 3) -> List[BranchPath]:
        partials = [([], 0, False, None)]
        for layer_name, options in LAYER_DEFINITIONS:
            expanded = []
            for decisions, cumulative, stopped, reason in partials:
                if stopped:
                    expanded.append((decisions, cumulative, stopped, reason))
                    continue
                proposals = []
                for neuron in self.per_layer.get(layer_name, []):
                    proposal = neuron.propose(features, decisions)
                    if proposal and proposal.selected in options:
                        proposal.candidates = list(options)
                        adjusted = proposal.confidence + int(max(min(neuron.score_value, 20), -20))
                        proposals.append((adjusted, proposal))
                if not proposals:
                    expanded.append((decisions, cumulative, True, f"missing_layer:{layer_name}"))
                    continue
                for adjusted, proposal in sorted(proposals, key=lambda item: (item[0], item[1].selected), reverse=True)[:top_k]:
                    next_decisions = decisions + [proposal]
                    stopped_now = proposal.selected in {"unsupported", "early_exit"}
                    reason_now = f"{layer_name}:{proposal.selected}" if stopped_now else None
                    expanded.append((next_decisions, cumulative + adjusted, stopped_now, reason_now))
            partials = sorted(expanded, key=lambda item: item[1], reverse=True)[:top_k]
        paths = []
        for decisions, cumulative, early_exit, reason in partials:
            paths.append(
                BranchPath(
                    decisions=decisions,
                    route_confidence=int(sum(d.confidence for d in decisions) / max(len(decisions), 1)),
                    atomic_experts=["ArithmeticExpressionExpert", "TargetIRBuilderExpert", "ConsistencyCheckExpert"] if not early_exit else [],
                    target_builder=decisions[-1].selected if decisions else "early_exit",
                    early_exit=early_exit,
                    unsupported_reason=reason,
                )
            )
        return paths

    def sample_candidate_paths(self, features: Dict, top_k: int = 3) -> List[CandidateGenome]:
        genomes: List[CandidateGenome] = []
        for candidate_index, path in enumerate(self.candidate_paths(features, top_k=top_k)):
            decisions_by_layer = {d.layer_name: d.selected for d in path.decisions}
            genomes.append(
                CandidateGenome(
                    genome_id=f"g{self.generation}:{candidate_index}:{abs(hash(tuple((d.layer_name, d.selected) for d in path.decisions))) % 10**8}",
                    branch_path=path,
                    atomic_expert_plan=path.atomic_experts,
                    slot_binding_policy=decisions_by_layer.get("slot_binding_policy", "unsupported"),
                    target_builder_policy=decisions_by_layer.get("target_builder", "early_exit"),
                    generation=self.generation,
                )
            )
        return genomes

    def evolve(self, candidate_records: List[CandidateRecord], seed: int = None, curriculum_plan=None):
        rng = random.Random(self.seed + self.generation + 1 if seed is None else seed)
        reward_by_neuron = defaultdict(float)
        for record in candidate_records:
            reward = record.fitness_report.total_fitness
            for decision in record.genome.branch_path.decisions:
                reward_by_neuron[decision.neuron_id] += reward
        next_layers: Dict[str, List[BranchNeuron]] = {}
        for layer_name, options in LAYER_DEFINITIONS:
            current = self.per_layer.get(layer_name, [])
            if curriculum_plan is not None and not curriculum_plan.can_mutate(layer_name):
                next_layers[layer_name] = [n.clone(n.neuron_id) for n in current]
                continue
            for neuron in current:
                if curriculum_plan is None or curriculum_plan.can_mutate(layer_name):
                    neuron.score_value += reward_by_neuron.get(neuron.neuron_id, 0.0)
            ranked = sorted(current, key=lambda n: n.score_value, reverse=True)
            layer_size = len(current)
            elites = [n.clone(f"{n.neuron_id}.elite") for n in ranked[: max(1, layer_size // 3)]]
            next_neurons = elites[:]
            _preserve_option_coverage(next_neurons, ranked, layer_name, options, rng)
            if curriculum_plan is None or curriculum_plan.can_mutate(layer_name):
                while len(next_neurons) < max(layer_size - len(options), 1):
                    parent = rng.choice(elites)
                    next_neurons.append(parent.mutate(rng))
            while len(next_neurons) < layer_size:
                option = rng.choice(options)
                next_neurons.append(make_random_neuron(layer_name, option, f"{layer_name}:immigrant:{rng.randint(0, 10**9)}", rng))
            next_layers[layer_name] = next_neurons[:layer_size]
        self.per_layer = next_layers
        self.generation += 1

    def summary(self) -> Dict:
        return {
            layer: {
                "count": len(neurons),
                "options": sorted({n.option for n in neurons}),
                "top_score": max((n.score_value for n in neurons), default=0.0),
            }
            for layer, neurons in sorted(self.per_layer.items())
        }


def _preserve_option_coverage(next_neurons, ranked, layer_name, options, rng):
    present = {n.option for n in next_neurons}
    for option in options:
        if option in present:
            continue
        donor = next((n for n in ranked if n.option == option), None)
        if donor:
            next_neurons.append(donor.clone(f"{donor.neuron_id}.coverage"))
        else:
            next_neurons.append(make_random_neuron(layer_name, option, f"{layer_name}:coverage:{option}", rng))
