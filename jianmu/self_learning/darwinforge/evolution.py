import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_chain import decision_pairs
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.hard_cases import HardCase, HardCaseBuffer
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


@dataclass
class DarwinForgeReport:
    dataset_size: int
    population_per_layer: int
    generations: int
    top_k_candidates: int
    compile_checks_per_generation: int = 0
    metrics_by_generation: List[Dict] = field(default_factory=list)
    population_summary: Dict = field(default_factory=dict)
    hard_case_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "dataset_size": self.dataset_size,
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k_candidates": self.top_k_candidates,
            "compile_checks_per_generation": self.compile_checks_per_generation,
            "metrics_by_generation": self.metrics_by_generation,
            "population_summary": self.population_summary,
            "hard_case_count": self.hard_case_count,
        }


class DarwinForgeTrainer:
    def __init__(
        self,
        population_per_layer: int = 16,
        generations: int = 30,
        top_k_candidates: int = 3,
        seed: int = 42,
        compile_checks_per_generation: int = 8,
    ):
        self.population_per_layer = population_per_layer
        self.generations = generations
        self.top_k_candidates = top_k_candidates
        self.seed = seed
        self.compile_checks_per_generation = compile_checks_per_generation
        self.population = LayerPreservedPopulation.initialize(population_per_layer=population_per_layer, seed=seed)
        self.synthesis = AtomicSynthesis()
        self.hard_cases = HardCaseBuffer()

    def train(self, dataset: List[Dict] = None) -> DarwinForgeReport:
        dataset = dataset or build_branchchain_toy_dataset()
        metrics_by_generation = []
        all_records: List[CandidateRecord] = []
        for generation in range(self.generations + 1):
            generation_records: List[CandidateRecord] = []
            winners: List[CandidateRecord] = []
            compile_checks_remaining = self.compile_checks_per_generation
            for task in dataset:
                features = extract_surface_features(task["input_text"])
                genomes = self.population.sample_candidate_paths(features, top_k=self.top_k_candidates)
                records = []
                for genome in genomes:
                    phenotype = self.synthesis.synthesize(genome, features)
                    should_check_compile = compile_checks_remaining > 0 and bool(phenotype.c_program)
                    fitness = compute_fitness(genome, phenotype, task, sandbox_optional=should_check_compile)
                    if should_check_compile:
                        compile_checks_remaining -= 1
                    records.append(CandidateRecord(genome, phenotype, fitness))
                winner = max(records, key=lambda rec: rec.fitness_report.total_fitness)
                winners.append(winner)
                generation_records.extend(records)
                if not _winner_succeeds(winner, task):
                    self.hard_cases.add(
                        HardCase(
                            input_text=task["input_text"],
                            target_ir=task["target_ir_canonical"],
                            expected_output=task["expected_output"],
                            best_candidate_ir=winner.phenotype.target_ir_canonical,
                            best_fitness=winner.fitness_report.total_fitness,
                            failure_reason=winner.phenotype.failure_reason,
                            generation=generation,
                            candidate_summary=winner.to_dict(),
                        )
                    )
            metrics = _metrics_for_generation(generation, winners, dataset)
            metrics_by_generation.append(metrics)
            all_records = generation_records
            if generation < self.generations:
                self.population.evolve(generation_records, seed=self.seed + generation)
        return DarwinForgeReport(
            dataset_size=len(dataset),
            population_per_layer=self.population_per_layer,
            generations=self.generations,
            top_k_candidates=self.top_k_candidates,
            compile_checks_per_generation=self.compile_checks_per_generation,
            metrics_by_generation=metrics_by_generation,
            population_summary=self.population.summary(),
            hard_case_count=len(self.hard_cases.items),
        )


def _winner_succeeds(record: CandidateRecord, task: Dict) -> bool:
    if not task["supported"]:
        return record.fitness_report.unsupported_correct
    return record.fitness_report.target_ir_exact_match and record.fitness_report.expected_output_match


def _metrics_for_generation(generation: int, winners: List[CandidateRecord], dataset: List[Dict]) -> Dict:
    total = max(len(winners), 1)
    missing_layers = 0
    branch_exact = 0
    target_exact = 0
    output_match = 0
    unsupported_correct = 0
    compile_checked = 0
    compile_success = 0
    run_success = 0
    wrong_branches = Counter()
    fitness_values = []
    for record, task in zip(winners, dataset):
        fitness = record.fitness_report
        fitness_values.append(fitness.total_fitness)
        target_pairs = task["target_branch_path"]
        pred_pairs = decision_pairs(record.genome.branch_path)
        branch_exact += int(pred_pairs == target_pairs)
        target_exact += int(fitness.target_ir_exact_match)
        output_match += int(fitness.expected_output_match)
        unsupported_correct += int(fitness.unsupported_correct)
        missing_layers += int(len(pred_pairs) < len(target_pairs))
        if fitness.compile_success is not None:
            compile_checked += 1
            compile_success += int(fitness.compile_success)
            run_success += int(fitness.run_success)
        for target in target_pairs:
            if target not in pred_pairs:
                selected = next((pair[1] for pair in pred_pairs if pair[0] == target[0]), "<missing>")
                wrong_branches[f"{target[0]}:{target[1]} -> {selected}"] += 1
    return {
        "generation": generation,
        "mean_fitness": round(sum(fitness_values) / total, 4),
        "best_fitness": round(max(fitness_values), 4),
        "target_ir_exact_match_rate": round(target_exact / total, 4),
        "expected_output_match_rate": round(output_match / total, 4),
        "unsupported_correct_rate": round(unsupported_correct / max(sum(1 for t in dataset if not t["supported"]), 1), 4),
        "checked_compile_success_rate": round(compile_success / max(compile_checked, 1), 4),
        "checked_run_success_rate": round(run_success / max(compile_checked, 1), 4),
        "branch_path_exact_match_rate": round(branch_exact / total, 4),
        "missing_layer_rate": round(missing_layers / total, 4),
        "most_common_wrong_branch_decisions": wrong_branches.most_common(10),
    }
