import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_chain import decision_pairs
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.attribution import attribute_candidate_error
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.curriculum import CurriculumPlan
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.hard_cases import HardCase, HardCaseBuffer
from jianmu.self_learning.darwinforge.hall_of_fame import HallOfFame
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


class CurriculumDarwinForgeTrainer:
    def __init__(
        self,
        population_per_layer: int = 16,
        generations: int = 40,
        top_k_candidates: int = 3,
        seed: int = 42,
        compile_checks_per_generation: int = 4,
        curriculum: CurriculumPlan = None,
    ):
        self.population_per_layer = population_per_layer
        self.generations = generations
        self.top_k_candidates = top_k_candidates
        self.seed = seed
        self.compile_checks_per_generation = compile_checks_per_generation
        self.curriculum = curriculum or CurriculumPlan()
        self.population = LayerPreservedPopulation.initialize(population_per_layer=population_per_layer, seed=seed)
        self.synthesis = AtomicSynthesis()
        self.hard_cases = HardCaseBuffer()
        self.hall_of_fame = HallOfFame()

    def train(self, dataset: List[Dict] = None) -> Dict:
        dataset = dataset or build_branchchain_toy_dataset()
        metrics_by_generation = []
        candidate_records_log = []
        for generation in range(self.generations + 1):
            self.curriculum.tick(generation)
            generation_records: List[CandidateRecord] = []
            winners: List[CandidateRecord] = []
            compile_checks_remaining = self.compile_checks_per_generation
            hard_case_attrs = []
            for task in dataset:
                features = extract_surface_features(task["input_text"])
                records = []
                for genome in self.population.sample_candidate_paths(features, top_k=self.top_k_candidates):
                    phenotype = self.synthesis.synthesize(genome, features)
                    should_check_compile = compile_checks_remaining > 0 and bool(phenotype.c_program)
                    fitness = compute_fitness(genome, phenotype, task, sandbox_optional=should_check_compile)
                    if should_check_compile:
                        compile_checks_remaining -= 1
                    record = CandidateRecord(genome, phenotype, fitness)
                    records.append(record)
                    generation_records.append(record)
                winner = max(records, key=lambda rec: rec.fitness_report.total_fitness)
                winners.append(winner)
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
                    hard_case_attrs.extend(attribute_candidate_error(winner, task))
            metrics = _metrics_for_generation(generation, winners, dataset)
            layer_metrics = _per_layer_metrics(winners, dataset)
            metrics["active_layer"] = self.curriculum.active_layer()
            metrics["per_layer_accuracy"] = {k: v["accuracy"] for k, v in layer_metrics.items()}
            metrics["per_layer_missing_rate"] = {k: v["missing_rate"] for k, v in layer_metrics.items()}
            metrics["frozen_layers"] = [layer for layer in self.curriculum.layer_order if self.curriculum.is_frozen(layer)]
            metrics["hard_case_attribution"] = _aggregate_attrs(hard_case_attrs, max(len(dataset), 1))
            for layer, values in layer_metrics.items():
                self.curriculum.update_layer_metrics(layer, values["accuracy"], values["missing_rate"], values["confidence_margin"])
            freeze_before = len(self.curriculum.freeze_events)
            unfreeze_before = len(self.curriculum.unfreeze_events)
            self.curriculum.maybe_freeze_active_layer()
            self.curriculum.maybe_unfreeze_from_hard_cases(metrics["hard_case_attribution"], threshold=0.65)
            self.curriculum.maybe_advance()
            metrics["freeze_events"] = self.curriculum.freeze_events[freeze_before:]
            metrics["unfreeze_events"] = self.curriculum.unfreeze_events[unfreeze_before:]
            metrics_by_generation.append(metrics)
            self.hall_of_fame.update(generation, metrics, self.population)
            candidate_records_log.extend(generation_records)
            if generation < self.generations:
                self.population.evolve(generation_records, seed=self.seed + generation, curriculum_plan=self.curriculum)
        return {
            "dataset_size": len(dataset),
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k_candidates": self.top_k_candidates,
            "compile_checks_per_generation": self.compile_checks_per_generation,
            "metrics_by_generation": metrics_by_generation,
            "curriculum": self.curriculum.to_dict(),
            "hall_of_fame": self.hall_of_fame.to_dict(),
            "population_summary": self.population.summary(),
            "hard_case_count": len(self.hard_cases.items),
            "candidate_records": candidate_records_log,
        }


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


def _per_layer_metrics(winners: List[CandidateRecord], dataset: List[Dict]) -> Dict[str, Dict]:
    totals = Counter()
    correct = Counter()
    missing = Counter()
    confidence_sum = Counter()
    for record, task in zip(winners, dataset):
        pred = {layer: value for layer, value in decision_pairs(record.genome.branch_path)}
        confidence = {d.layer_name: d.confidence for d in record.genome.branch_path.decisions}
        for layer, expected in task["target_branch_path"]:
            totals[layer] += 1
            if layer not in pred:
                missing[layer] += 1
            elif pred[layer] == expected:
                correct[layer] += 1
            confidence_sum[layer] += confidence.get(layer, 0)
    result = {}
    for layer, total in totals.items():
        result[layer] = {
            "accuracy": round(correct[layer] / max(total, 1), 4),
            "missing_rate": round(missing[layer] / max(total, 1), 4),
            "confidence_margin": round(confidence_sum[layer] / max(total, 1) / 100.0, 4),
        }
    return result


def _aggregate_attrs(attrs, denominator: int) -> Dict[str, Dict]:
    count = Counter()
    severity = Counter()
    for attr in attrs:
        count[attr.layer_name] += 1
        severity[attr.layer_name] += attr.severity
    return {
        layer: {
            "error_count": value,
            "error_rate": round(value / denominator, 4),
            "severity": round(severity[layer] / denominator, 4),
        }
        for layer, value in count.items()
    }
