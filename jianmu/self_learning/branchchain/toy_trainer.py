import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from jianmu.self_learning.branchchain.branch_chain import BranchChainRouter, LAYER_DEFINITIONS, decision_pairs
from jianmu.self_learning.branchchain.branch_neuron import BranchNeuron, make_random_neuron, make_seed_neurons
from jianmu.self_learning.branchchain.path_reward import compute_path_reward, distribute_reward
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset


@dataclass
class ToyTrainingReport:
    generation_count: int
    population_size: int
    dataset_size: int
    metrics_by_generation: List[Dict] = field(default_factory=list)
    final_population_summary: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "generation_count": self.generation_count,
            "population_size": self.population_size,
            "dataset_size": self.dataset_size,
            "metrics_by_generation": self.metrics_by_generation,
            "final_population_summary": self.final_population_summary,
        }


class BranchChainToyTrainer:
    def __init__(self, population_size: int = 128, generations: int = 30, seed: int = 42):
        self.population_size = population_size
        self.generations = generations
        self.seed = seed
        self.rng = random.Random(seed)
        self.population = initialize_population(population_size, self.rng)

    def train(self, dataset: Optional[List[Dict]] = None) -> ToyTrainingReport:
        dataset = dataset or build_branchchain_toy_dataset()
        metrics_by_generation: List[Dict] = []
        for generation in range(self.generations + 1):
            metrics, neuron_rewards = evaluate_population(self.population, dataset)
            metrics["generation"] = generation
            metrics_by_generation.append(metrics)
            for neuron in self.population:
                neuron.score_value += neuron_rewards.get(neuron.neuron_id, 0.0)
            if generation < self.generations:
                self.population = evolve_population(self.population, self.population_size, self.rng)

        final_summary = [
            {
                "neuron_id": neuron.neuron_id,
                "layer_name": neuron.layer_name,
                "option": neuron.option,
                "score": round(neuron.score_value, 4),
                "mutation_count": neuron.mutation_count,
            }
            for neuron in sorted(self.population, key=lambda n: n.score_value, reverse=True)[:20]
        ]
        return ToyTrainingReport(
            generation_count=self.generations,
            population_size=self.population_size,
            dataset_size=len(dataset),
            metrics_by_generation=metrics_by_generation,
            final_population_summary=final_summary,
        )


def initialize_population(population_size: int, rng: random.Random) -> List[BranchNeuron]:
    population: List[BranchNeuron] = []
    for layer_name, options in LAYER_DEFINITIONS:
        population.extend(make_seed_neurons(layer_name, options, len(population)))
    while len(population) < population_size:
        layer_name, options = rng.choice(LAYER_DEFINITIONS)
        option = rng.choice(options)
        population.append(make_random_neuron(layer_name, option, f"immigrant:{len(population)}", rng))
    return population[:population_size]


def evaluate_population(population: List[BranchNeuron], dataset: List[Dict]) -> Tuple[Dict, Dict[str, float]]:
    router = BranchChainRouter(population=population)
    totals = Counter()
    per_layer_total = Counter()
    per_layer_correct = Counter()
    wrong_branches = Counter()
    neuron_rewards = defaultdict(float)
    rewards: List[float] = []

    for sample in dataset:
        features = extract_surface_features(sample["input_text"])
        branch_path = router.route(features)
        predicted_ir, predicted_output = build_target_from_branch_path(branch_path, features)
        reward, components = compute_path_reward(
            branch_path=branch_path,
            target_branch_path=sample["target_branch_path"],
            predicted_target_ir=predicted_ir,
            predicted_expected_output=predicted_output,
            target_ir_canonical=sample["target_ir_canonical"],
            expected_output=sample["expected_output"],
            supported=sample["supported"],
        )
        distribute_reward(branch_path, reward)
        rewards.append(reward)
        totals["branch_path_exact"] += int(components["branch_path_exact_match"])
        totals["target_ir_exact"] += int(components["target_ir_exact_match"])
        totals["early_exit_correct"] += int((not sample["supported"]) == branch_path.early_exit)
        totals["pred_early_exit"] += int(branch_path.early_exit)
        totals["true_unsupported"] += int(not sample["supported"])
        totals["early_exit_tp"] += int((not sample["supported"]) and branch_path.early_exit)
        totals["early_exit_fp"] += int(sample["supported"] and branch_path.early_exit)
        totals["early_exit_fn"] += int((not sample["supported"]) and not branch_path.early_exit)

        predicted_pairs = decision_pairs(branch_path)
        target_pairs = sample["target_branch_path"]
        for target in target_pairs:
            layer = target[0]
            per_layer_total[layer] += 1
            match = target in predicted_pairs
            per_layer_correct[layer] += int(match)
            if not match:
                selected = next((pair[1] for pair in predicted_pairs if pair[0] == layer), "<missing>")
                wrong_branches[f"{layer}:{target[1]} -> {selected}"] += 1
        for decision in branch_path.decisions:
            neuron_rewards[decision.neuron_id] += decision.reward

    size = max(len(dataset), 1)
    precision = totals["early_exit_tp"] / max(totals["early_exit_tp"] + totals["early_exit_fp"], 1)
    recall = totals["early_exit_tp"] / max(totals["early_exit_tp"] + totals["early_exit_fn"], 1)
    metrics = {
        "mean_reward": round(sum(rewards) / size, 4),
        "branch_path_accuracy": round(totals["branch_path_exact"] / size, 4),
        "target_ir_accuracy": round(totals["target_ir_exact"] / size, 4),
        "early_exit_accuracy": round(totals["early_exit_correct"] / size, 4),
        "early_exit_precision": round(precision, 4),
        "early_exit_recall": round(recall, 4),
        "per_layer_accuracy": {
            layer: round(per_layer_correct[layer] / count, 4)
            for layer, count in sorted(per_layer_total.items())
        },
        "most_common_wrong_branch_decisions": wrong_branches.most_common(10),
    }
    return metrics, dict(neuron_rewards)


def evolve_population(population: List[BranchNeuron], population_size: int, rng: random.Random) -> List[BranchNeuron]:
    ranked = sorted(population, key=lambda neuron: neuron.score_value, reverse=True)
    elite_count = max(1, int(population_size * 0.30))
    elites = [neuron.clone(f"{neuron.neuron_id}.elite") for neuron in ranked[:elite_count]]
    next_population = elites[:]
    while len(next_population) < int(population_size * 0.80):
        parent = rng.choice(elites)
        next_population.append(parent.mutate(rng))
    while len(next_population) < population_size:
        layer_name, options = rng.choice(LAYER_DEFINITIONS)
        next_population.append(make_random_neuron(layer_name, rng.choice(options), f"immigrant:{rng.randint(0, 10**9)}", rng))
    return next_population[:population_size]


def build_target_from_branch_path(branch_path, features: Dict) -> Tuple[Optional[str], Optional[str]]:
    if branch_path.early_exit:
        return None, None
    decisions = {decision.layer_name: decision.selected for decision in branch_path.decisions}
    if decisions.get("target_builder") != "canonical_arithmetic_targetir":
        return None, None
    numbers = features.get("signed_numbers", [])
    ops = features.get("operator_sequence", "")
    if len(numbers) < 2 or not ops:
        return None, None
    try:
        canonical, value = _canonical_from_surface(numbers, ops, features.get("contains_parentheses", False))
        return canonical, f"{value}\n"
    except Exception:
        return None, None


def _canonical_from_surface(numbers: List[int], ops: str, has_parentheses: bool) -> Tuple[str, int]:
    if has_parentheses and len(numbers) >= 3 and "*" in ops:
        left = f"add(lit({numbers[0]}),lit({numbers[1]}))"
        value = (numbers[0] + numbers[1]) * numbers[2]
        return f"mul({left},lit({numbers[2]}))", value
    if len(numbers) >= 3 and len(ops) >= 2:
        if ops[:2] == "++":
            return f"add(add(lit({numbers[0]}),lit({numbers[1]})),lit({numbers[2]}))", numbers[0] + numbers[1] + numbers[2]
        if ops[:2] == "+*":
            return f"add(lit({numbers[0]}),mul(lit({numbers[1]}),lit({numbers[2]})))", numbers[0] + numbers[1] * numbers[2]
        if ops[:2] == "*+":
            return f"add(mul(lit({numbers[0]}),lit({numbers[1]})),lit({numbers[2]}))", numbers[0] * numbers[1] + numbers[2]
    op = ops[0]
    a, b = numbers[0], numbers[1]
    if op == "+":
        return f"add(lit({a}),lit({b}))", a + b
    if op == "-":
        return f"sub(lit({a}),lit({b}))", a - b
    if op == "*":
        return f"mul(lit({a}),lit({b}))", a * b
    if op == "/":
        if b == 0 or a % b != 0:
            raise ValueError("unsupported division")
        return f"div(lit({a}),lit({b}))", int(a / b)
    raise ValueError("unknown operator")

