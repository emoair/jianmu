import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from jianmu.sandbox import Sandbox
from jianmu.self_learning.ir_tokens import IRToken, SUPPORTED_TOKEN_TYPES, tokens_to_c_code
from jianmu.self_learning.prefix_dataset import PrefixTrainingTask
from jianmu.self_learning.prefix_neuron import PrefixNeuron, TokenProposal
from jianmu.self_learning.prefix_state import PrefixState


RULE_TYPES = [
    "start_include",
    "after_include_main",
    "emit_first_literal",
    "emit_second_literal",
    "emit_add_after_two_literals",
    "emit_print_after_add",
    "emit_end_after_print",
    "random_token",
]
VALUE_POLICIES = ["none", "first_number", "second_number", "constant"]
TOKEN_TYPES = sorted(SUPPORTED_TOKEN_TYPES)


@dataclass
class EvolutionReport:
    generation_count: int
    best_sequence_accuracy_by_generation: List[float] = field(default_factory=list)
    full_sequence_success_by_generation: List[float] = field(default_factory=list)
    compile_success_by_generation: List[float] = field(default_factory=list)
    task_success_by_generation: List[float] = field(default_factory=list)
    best_neurons: List[Dict] = field(default_factory=list)
    final_population_summary: List[Dict] = field(default_factory=list)


class PrefixEvolutionTrainer:
    def __init__(
        self,
        training_tasks: List[PrefixTrainingTask],
        population: List[PrefixNeuron],
        generations: int = 30,
        seed: int = 42,
        max_steps: int = 7,
        top_k_retry: int = 2,
    ):
        self.training_tasks = list(training_tasks)
        self.population = list(population)
        self.generations = generations
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.top_k_retry = top_k_retry
        self.sandbox = Sandbox()

    def train(self) -> EvolutionReport:
        report = EvolutionReport(generation_count=self.generations)
        for _ in range(self.generations):
            metrics = self._run_generation()
            report.best_sequence_accuracy_by_generation.append(metrics["sequence_accuracy"])
            report.full_sequence_success_by_generation.append(metrics["full_sequence_success"])
            report.compile_success_by_generation.append(metrics["compile_success"])
            report.task_success_by_generation.append(metrics["task_success"])
            self.population = self._evolve_population()

        ranked = sorted(self.population, key=lambda neuron: neuron.score, reverse=True)
        report.best_neurons = [_neuron_summary(neuron) for neuron in ranked[:10]]
        report.final_population_summary = [_neuron_summary(neuron) for neuron in ranked]
        return report

    def _run_generation(self) -> Dict[str, float]:
        correct_prefixes = 0
        total_prefixes = 0
        full_sequences = 0
        compile_successes = 0
        task_successes = 0

        for task in self.training_tasks:
            sequence, participants, matched = self._generate_sequence_for_task(task)
            correct_prefixes += matched
            total_prefixes += len(task.target_tokens)

            if sequence == task.target_tokens:
                full_sequences += 1
                sandbox_result = self._validate_sequence(task, sequence)
                if sandbox_result.compile_success and sandbox_result.run_success:
                    compile_successes += 1
                if sandbox_result.compile_success and sandbox_result.run_success and sandbox_result.stdout == task.expected_output:
                    task_successes += 1
                    self._reward_path(participants, 5)
                elif sandbox_result.error_type == "no_compiler":
                    pass
                else:
                    self._reward_path(participants, -3)

        task_count = max(1, len(self.training_tasks))
        return {
            "sequence_accuracy": round(correct_prefixes / max(1, total_prefixes), 4),
            "full_sequence_success": round(full_sequences / task_count, 4),
            "compile_success": round(compile_successes / task_count, 4),
            "task_success": round(task_successes / task_count, 4),
        }

    def _generate_sequence_for_task(
        self,
        task: PrefixTrainingTask,
    ) -> Tuple[List[IRToken], List[str], int]:
        prefix: List[IRToken] = []
        participants: List[str] = []
        matched = 0
        for step in range(min(self.max_steps, len(task.target_tokens))):
            state = PrefixState(task.input_text, list(prefix), step)
            proposals = [neuron.propose(state) for neuron in self.population]
            proposals.sort(key=lambda proposal: proposal.confidence, reverse=True)
            expected_token = task.target_tokens[step]
            accepted = self._accept_matching_proposal(proposals, expected_token)
            if accepted is None:
                return prefix, participants, matched
            proposal, neuron = accepted
            neuron.score += 1
            participants.append(neuron.neuron_id)
            prefix.append(proposal.token)
            matched += 1
        return prefix, participants, matched

    def _accept_matching_proposal(
        self,
        proposals: List[TokenProposal],
        expected_token: IRToken,
    ):
        max_attempts = self.top_k_retry + 1
        for proposal in proposals[:max_attempts]:
            neuron = self._neuron_by_id(proposal.neuron_id)
            if proposal.token == expected_token:
                return proposal, neuron
            neuron.score -= 1
        return None

    def _validate_sequence(self, task: PrefixTrainingTask, sequence: List[IRToken]):
        code = tokens_to_c_code(sequence)
        return self.sandbox.run(code)

    def _reward_path(self, participants: List[str], amount: int):
        seen = set()
        for neuron_id in participants:
            if neuron_id in seen:
                continue
            self._neuron_by_id(neuron_id).score += amount
            seen.add(neuron_id)

    def _evolve_population(self) -> List[PrefixNeuron]:
        target_size = len(self.population)
        survivors_count = max(1, int(target_size * 0.3))
        ranked = sorted(self.population, key=lambda neuron: neuron.score, reverse=True)
        canonical_ids = [
            "n_include",
            "n_main",
            "n_first_literal",
            "n_second_literal",
            "n_add",
            "n_print",
            "n_end",
        ]
        by_id = {neuron.neuron_id: neuron for neuron in ranked}
        survivors = [
            by_id[neuron_id].clone(neuron_id)
            for neuron_id in canonical_ids
            if neuron_id in by_id
        ]
        seen_signatures = {
            (neuron.rule_type, neuron.target_token_type, neuron.target_value_policy)
            for neuron in survivors
        }
        for neuron in ranked:
            if neuron.neuron_id in canonical_ids:
                continue
            signature = (neuron.rule_type, neuron.target_token_type, neuron.target_value_policy)
            if signature in seen_signatures:
                continue
            survivors.append(neuron.clone(neuron.neuron_id))
            seen_signatures.add(signature)
            if len(survivors) >= survivors_count:
                break
        for neuron in ranked:
            if len(survivors) >= survivors_count:
                break
            survivors.append(neuron.clone(neuron.neuron_id))
        next_population = list(survivors)

        clone_index = 0
        while len(next_population) < target_size:
            if survivors and len(next_population) < target_size * 0.8:
                parent = survivors[clone_index % len(survivors)]
                child = parent.clone(f"{parent.neuron_id}_m{parent.mutation_count + 1}_{len(next_population)}")
                self._mutate(child)
                next_population.append(child)
                clone_index += 1
            else:
                next_population.append(_random_neuron(self.rng, f"random_{len(next_population)}"))
        return next_population

    def _mutate(self, neuron: PrefixNeuron):
        neuron.weight = max(0, min(100, neuron.weight + self.rng.randint(-5, 5)))
        if self.rng.random() < 0.1:
            neuron.rule_type = self.rng.choice(RULE_TYPES)
        if self.rng.random() < 0.1:
            neuron.target_value_policy = self.rng.choice(VALUE_POLICIES)
        neuron.mutation_count += 1

    def _neuron_by_id(self, neuron_id: str) -> PrefixNeuron:
        for neuron in self.population:
            if neuron.neuron_id == neuron_id:
                return neuron
        raise KeyError(neuron_id)


def build_initial_population(population_size: int = 64, seed: int = 42) -> List[PrefixNeuron]:
    seeded = [
        PrefixNeuron("n_include", "start_include", "INCLUDE_STDIO", "none", 30),
        PrefixNeuron("n_main", "after_include_main", "MAIN_BEGIN", "none", 30),
        PrefixNeuron("n_first_literal", "emit_first_literal", "LITERAL_INT", "first_number", 30),
        PrefixNeuron("n_second_literal", "emit_second_literal", "LITERAL_INT", "second_number", 30),
        PrefixNeuron("n_add", "emit_add_after_two_literals", "ADD", "none", 30),
        PrefixNeuron("n_print", "emit_print_after_add", "PRINT_EXPR", "none", 30),
        PrefixNeuron("n_end", "emit_end_after_print", "MAIN_END", "none", 30),
    ]
    rng = random.Random(seed)
    population = list(seeded)
    while len(population) < population_size:
        population.append(_random_neuron(rng, f"random_{len(population)}"))
    return population[:population_size]


def _random_neuron(rng: random.Random, neuron_id: str) -> PrefixNeuron:
    return PrefixNeuron(
        neuron_id=neuron_id,
        rule_type=rng.choice(RULE_TYPES),
        target_token_type=rng.choice(TOKEN_TYPES),
        target_value_policy=rng.choice(VALUE_POLICIES),
        weight=rng.randint(0, 35),
    )


def _neuron_summary(neuron: PrefixNeuron) -> Dict:
    return {
        "neuron_id": neuron.neuron_id,
        "rule_type": neuron.rule_type,
        "target_token_type": neuron.target_token_type,
        "target_value_policy": neuron.target_value_policy,
        "weight": neuron.weight,
        "score": neuron.score,
        "mutation_count": neuron.mutation_count,
    }
