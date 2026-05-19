import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_chain import decision_pairs
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.attribution import attribute_candidate_error
from jianmu.self_learning.darwinforge.backtracking_curriculum import PerfectLayerCurriculumPlan
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.curriculum import CurriculumPlan
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.freezing import required_correct_count
from jianmu.self_learning.darwinforge.hard_cases import HardCase, HardCaseBuffer
from jianmu.self_learning.darwinforge.hall_of_fame import HallOfFame
from jianmu.self_learning.darwinforge.paraphrase import apply_group_fitness, compute_group_metrics, group_dataset_by_paraphrase
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.reranking import (
    collect_pruning_candidates,
    rerank_candidates_for_sample,
    select_group_beam,
)


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
            records_by_task = []
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
                records_by_task.append(records)
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
            metrics.update(_candidate_recall_metrics(records_by_task, dataset, self.curriculum.criteria))
            layer_metrics = _per_layer_metrics(winners, dataset)
            metrics["active_layer"] = self.curriculum.active_layer()
            metrics["per_layer_accuracy"] = {k: v["accuracy"] for k, v in layer_metrics.items()}
            metrics["per_layer_missing_rate"] = {k: v["missing_rate"] for k, v in layer_metrics.items()}
            metrics["frozen_layers"] = [layer for layer in self.curriculum.layer_order if self.curriculum.is_frozen(layer)]
            metrics["hard_case_attribution"] = _aggregate_attrs(hard_case_attrs, max(len(dataset), 1))
            for layer, values in layer_metrics.items():
                self.curriculum.update_layer_metrics(layer, values["accuracy"], values["missing_rate"], values["confidence_margin"])
            active = self.curriculum.active_layer()
            active_search_metrics = {
                "accuracy": metrics["per_layer_winner_accuracy"].get(active, 0.0),
                "recall_at_k": metrics["per_layer_recall_at_k"].get(active, 0.0),
                "missing_rate": metrics["per_layer_missing_rate"].get(active, 1.0),
                "correct_count": metrics["per_layer_correct_count"].get(active, 0),
                "total_count": metrics["per_layer_total_count"].get(active, 0),
            }
            self.curriculum.threshold_controller.update(active, active_search_metrics)
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


class ParaphraseInvariantDarwinForgeTrainer:
    def __init__(
        self,
        population_per_layer: int = 16,
        generations: int = 80,
        top_k_candidates: int = 3,
        seed: int = 42,
        compile_checks_per_generation: int = 0,
    ):
        self.population_per_layer = population_per_layer
        self.generations = generations
        self.top_k_candidates = top_k_candidates
        self.seed = seed
        self.compile_checks_per_generation = compile_checks_per_generation
        self.population = LayerPreservedPopulation.initialize(population_per_layer=population_per_layer, seed=seed)
        self.synthesis = AtomicSynthesis()

    def train(self, dataset: List[Dict]) -> Dict:
        groups = group_dataset_by_paraphrase(dataset)
        ordered_samples = [sample for group_id in sorted(groups) for sample in groups[group_id].samples]
        metrics_by_generation = []
        candidate_records_log = []
        best_metrics = None
        for generation in range(self.generations + 1):
            winners = []
            generation_records = []
            for task in ordered_samples:
                features = extract_surface_features(task["input_text"])
                records = []
                for candidate_index, genome in enumerate(self.population.sample_candidate_paths(features, top_k=self.top_k_candidates)):
                    phenotype = self.synthesis.synthesize(genome, features)
                    fitness = compute_fitness(
                        genome,
                        phenotype,
                        task,
                        sandbox_optional=candidate_index < self.compile_checks_per_generation,
                    )
                    records.append(CandidateRecord(genome, phenotype, fitness))
                winner = max(records, key=lambda record: record.fitness_report.total_fitness)
                winners.append(winner)
                generation_records.extend(records)
            group_metrics_before = compute_group_metrics(winners, ordered_samples)
            group_metrics_after = apply_group_fitness(winners, ordered_samples)
            metrics = _metrics_for_generation(generation, winners, ordered_samples)
            metrics.update(
                {
                    "sample_target_ir_exact_match": group_metrics_after["sample_target_ir_exact_match"],
                    "group_targetir_consistency": group_metrics_after["group_targetir_consistency"],
                    "group_targetir_exact_match": group_metrics_after["group_targetir_exact_match"],
                    "cross_mode_consistency": group_metrics_after["cross_mode_consistency"],
                    "paraphrase_collapse_rate": group_metrics_after["paraphrase_collapse_rate"],
                    "ood_rejection_rate": group_metrics_after["ood_rejection_rate"],
                    "ood_false_accept_rate": group_metrics_after["ood_false_accept_rate"],
                    "supported_all_rejected_group_count": group_metrics_after["supported_all_rejected_group_count"],
                    "group_inconsistent_count": group_metrics_after["group_inconsistent_count"],
                    "group_metrics_before_reward": group_metrics_before,
                    "representative_group_predictions": group_metrics_after["representative_group_predictions"],
                }
            )
            metrics_by_generation.append(metrics)
            if best_metrics is None or _paraphrase_metric_key(metrics) > _paraphrase_metric_key(best_metrics):
                best_metrics = metrics
            candidate_records_log.extend(generation_records)
            if generation < self.generations:
                self.population.evolve(winners, seed=self.seed + generation)
        return {
            "dataset_size": len(ordered_samples),
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k_candidates": self.top_k_candidates,
            "compile_checks_per_generation": self.compile_checks_per_generation,
            "supported_paraphrase_group_count": sum(1 for group in groups.values() if group.supported),
            "ood_count": sum(1 for sample in ordered_samples if sample.get("input_mode", "").startswith("ood_")),
            "input_mode_counts": _count_values(sample.get("input_mode", "") for sample in ordered_samples),
            "metrics_by_generation": metrics_by_generation,
            "best_metrics": best_metrics or {},
            "population_summary": self.population.summary(),
            "candidate_records": candidate_records_log,
        }


class HindsightReRankingDarwinForgeTrainer:
    def __init__(
        self,
        population_per_layer: int = 16,
        generations: int = 80,
        top_k_candidates: int = 3,
        beam_width: int = 5,
        seed: int = 42,
        compile_checks_per_generation: int = 0,
    ):
        self.population_per_layer = population_per_layer
        self.generations = generations
        self.top_k_candidates = top_k_candidates
        self.beam_width = beam_width
        self.seed = seed
        self.compile_checks_per_generation = compile_checks_per_generation
        self.population = LayerPreservedPopulation.initialize(population_per_layer=population_per_layer, seed=seed)
        self.synthesis = AtomicSynthesis()

    def train(self, dataset: List[Dict]) -> Dict:
        groups = group_dataset_by_paraphrase(dataset)
        ordered_groups = [groups[group_id] for group_id in sorted(groups)]
        metrics_by_generation = []
        candidate_records_log = []
        pruning_log = []
        best_metrics = None
        for generation in range(self.generations + 1):
            group_selected_records = []
            group_all_records = []
            group_rank_records = []
            beam_results = []
            for group in ordered_groups:
                records_by_sample = []
                for task in group.samples:
                    features = extract_surface_features(task["input_text"])
                    records = []
                    for candidate_index, genome in enumerate(self.population.sample_candidate_paths(features, top_k=self.top_k_candidates)):
                        phenotype = self.synthesis.synthesize(genome, features)
                        fitness = compute_fitness(
                            genome,
                            phenotype,
                            task,
                            sandbox_optional=candidate_index < self.compile_checks_per_generation,
                        )
                        records.append(CandidateRecord(genome, phenotype, fitness))
                    records_by_sample.append(records)
                    group_all_records.extend(records)
                    group_rank_records.extend(rerank_candidates_for_sample(records, task))
                beam = select_group_beam(records_by_sample, group.samples, beam_width=self.beam_width)
                beam_results.append(beam)
                records_by_id = {record.genome.genome_id: record for records in records_by_sample for record in records}
                selected = [records_by_id[candidate_id] for candidate_id in beam.selected_candidate_ids if candidate_id in records_by_id]
                self._apply_hindsight_feedback(selected, group_all_records, group_rank_records, beam)
                group_selected_records.extend(selected)
            pruning_candidates = collect_pruning_candidates(group_rank_records, group_all_records)
            pruning_log.extend(pruning_candidates)
            metrics = _hindsight_metrics(generation, group_selected_records, group_all_records, group_rank_records, beam_results, dataset)
            metrics_by_generation.append(metrics)
            if best_metrics is None or _hindsight_metric_key(metrics) > _hindsight_metric_key(best_metrics):
                best_metrics = metrics
            candidate_records_log.extend(group_all_records)
            if generation < self.generations:
                self.population.evolve(group_all_records, seed=self.seed + generation)
        return {
            "dataset_size": len(dataset),
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k_candidates": self.top_k_candidates,
            "beam_width": self.beam_width,
            "compile_checks_per_generation": self.compile_checks_per_generation,
            "supported_group_count": sum(1 for group in groups.values() if group.supported),
            "ood_count": sum(1 for sample in dataset if sample.get("input_mode", "").startswith("ood_")),
            "metrics_by_generation": metrics_by_generation,
            "best_metrics": best_metrics or {},
            "population_summary": self.population.summary(),
            "candidate_records": candidate_records_log,
            "pruning_candidates": [item.to_dict() for item in pruning_log[-200:]],
        }

    def _apply_hindsight_feedback(self, selected, all_records, rank_records, beam):
        selected_ids = {record.genome.genome_id for record in selected}
        by_id = {record.genome.genome_id: record for record in all_records}
        for record in selected:
            _add_component(record, "group_beam_selected_bonus", 1.0)
            if beam.group_targetir_exact_match:
                _add_component(record, "group_beam_exact_match_bonus", 4.0)
            elif beam.collapse_detected:
                _add_component(record, "collapse_penalty", -4.0)
        for rank in rank_records:
            record = by_id.get(rank.candidate_id)
            if not record:
                continue
            if rank.quadrant == "low_score_correct":
                _add_component(record, "rerank_bonus", 3.0)
            elif rank.quadrant == "high_score_wrong":
                _add_component(record, "pruning_penalty", -3.0)
            elif rank.candidate_id in selected_ids and rank.quadrant == "high_score_correct":
                _add_component(record, "high_score_correct_reinforcement", 1.0)


class PerfectLayerBacktrackingTrainer:
    def __init__(
        self,
        population_per_layer: int = 16,
        generations: int = 120,
        top_k_candidates: int = 3,
        seed: int = 42,
        curriculum: PerfectLayerCurriculumPlan = None,
        compile_checks_per_generation: int = 0,
    ):
        self.population_per_layer = population_per_layer
        self.generations = generations
        self.top_k_candidates = top_k_candidates
        self.seed = seed
        self.compile_checks_per_generation = compile_checks_per_generation
        self.curriculum = curriculum or PerfectLayerCurriculumPlan()
        self.population = LayerPreservedPopulation.initialize(population_per_layer=population_per_layer, seed=seed)
        self.synthesis = AtomicSynthesis()

    def train(self, dataset: List[Dict]) -> Dict:
        metrics_by_generation = []
        candidate_records_log = []
        best_target_ir = 0.0
        for generation in range(self.generations + 1):
            winners = []
            records_by_task = []
            generation_records = []
            rank_records = []
            for task in dataset:
                features = extract_surface_features(task["input_text"])
                records = []
                for candidate_index, genome in enumerate(self.population.sample_candidate_paths(features, top_k=self.top_k_candidates)):
                    phenotype = self.synthesis.synthesize(genome, features)
                    fitness = compute_fitness(
                        genome,
                        phenotype,
                        task,
                        sandbox_optional=candidate_index < self.compile_checks_per_generation,
                    )
                    records.append(CandidateRecord(genome, phenotype, fitness))
                ranks = rerank_candidates_for_sample(records, task)
                winner = next(record for record in records if record.genome.genome_id == ranks[0].candidate_id)
                winners.append(winner)
                records_by_task.append(records)
                generation_records.extend(records)
                rank_records.extend(ranks)
            per_layer = _perfect_per_layer_metrics(winners, records_by_task, dataset)
            for layer, values in per_layer.items():
                self.curriculum.update_layer_metrics(
                    layer,
                    values["accuracy"],
                    values["recall_at_k"],
                    values["missing_rate"],
                    values["correct_count"],
                    values["total_count"],
                    generation,
                )
            self.curriculum.step(generation)
            base = _metrics_for_generation(generation, winners, dataset)
            best_target_ir = max(best_target_ir, base["target_ir_exact_match_rate"])
            quadrants = Counter(rank.quadrant for rank in rank_records)
            metrics = {
                "generation": generation,
                "active_layer": self.curriculum.active_layer(),
                "trainable_layers": self.curriculum.trainable_layers(),
                "frozen_layers": [layer for layer in self.curriculum.layer_order if self.curriculum.is_frozen(layer)],
                "perfect_layer_count": sum(1 for layer in self.curriculum.layer_order if self.curriculum.is_frozen(layer)),
                "per_layer_accuracy": {layer: values["accuracy"] for layer, values in per_layer.items()},
                "per_layer_correct_count": {layer: values["correct_count"] for layer, values in per_layer.items()},
                "per_layer_required_count": {layer: values["total_count"] for layer, values in per_layer.items()},
                "per_layer_recall_at_k": {layer: values["recall_at_k"] for layer, values in per_layer.items()},
                "target_ir_exact_match": base["target_ir_exact_match_rate"],
                "target_ir_exact_match_best": best_target_ir,
                "low_score_correct_count": quadrants.get("low_score_correct", 0),
                "high_score_wrong_count": quadrants.get("high_score_wrong", 0),
                "backtracking_event_count": len(self.curriculum.backtracking_events),
                "backtracking_events": [event.to_dict() for event in self.curriculum.backtracking_events],
                "freeze_events": list(self.curriculum.freeze_events),
                "blocked_layer_count": len(self.curriculum.blocked_layers),
                "blocked_layers": list(self.curriculum.blocked_layers),
            }
            metrics_by_generation.append(metrics)
            candidate_records_log.extend(generation_records)
            if generation < self.generations:
                self.population.evolve(generation_records, seed=self.seed + generation, curriculum_plan=self.curriculum)
        return {
            "dataset_size": len(dataset),
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k_candidates": self.top_k_candidates,
            "curriculum": self.curriculum.to_dict(),
            "metrics_by_generation": metrics_by_generation,
            "population_summary": self.population.summary(),
            "candidate_records": candidate_records_log,
        }


def _winner_succeeds(record: CandidateRecord, task: Dict) -> bool:
    if not task["supported"]:
        return record.fitness_report.unsupported_correct
    return record.fitness_report.target_ir_exact_match and record.fitness_report.expected_output_match


def _paraphrase_metric_key(metrics: Dict):
    return (
        metrics.get("group_targetir_exact_match", 0.0),
        metrics.get("sample_target_ir_exact_match", 0.0),
        metrics.get("cross_mode_consistency", 0.0),
        -metrics.get("paraphrase_collapse_rate", 1.0),
        metrics.get("ood_rejection_rate", 0.0),
    )


def _count_values(values) -> Dict[str, int]:
    counter = Counter(values)
    return dict(sorted(counter.items()))


def _add_component(record: CandidateRecord, name: str, delta: float):
    record.fitness_report.total_fitness = round(record.fitness_report.total_fitness + delta, 4)
    record.fitness_report.components[name] = round(record.fitness_report.components.get(name, 0.0) + delta, 4)


def _hindsight_metric_key(metrics: Dict):
    return (
        metrics.get("group_beam_exact_match", 0.0),
        metrics.get("reranked_sample_exact_match", 0.0),
        metrics.get("ood_rejection_rate", 0.0),
        -metrics.get("paraphrase_collapse_rate", 1.0),
    )


def _hindsight_metrics(generation: int, selected_records: List[CandidateRecord], all_records: List[CandidateRecord], rank_records, beam_results, dataset: List[Dict]) -> Dict:
    total = max(len(dataset), 1)
    single_winner_exact = 0
    reranked_exact = 0
    rerank_improvement = 0
    rerank_regression = 0
    by_sample = defaultdict(list)
    for rank in rank_records:
        by_sample[rank.sample_id].append(rank)
    for sample_id, ranks in by_sample.items():
        original_top = next(item for item in ranks if item.original_rank == 0)
        reranked_top = next(item for item in ranks if item.rerank_rank == 0)
        single_winner_exact += int(original_top.exact_match)
        reranked_exact += int(reranked_top.exact_match)
        rerank_improvement += int((not original_top.exact_match) and reranked_top.exact_match)
        rerank_regression += int(original_top.exact_match and not reranked_top.exact_match)
    supported_beams = [beam for beam in beam_results if any(sample["paraphrase_group"] == beam.group_id and sample["supported"] for sample in dataset)]
    group_beam_exact = sum(1 for beam in supported_beams if beam.group_targetir_exact_match)
    group_beam_consistent = sum(1 for beam in supported_beams if beam.group_targetir_consistency)
    wrong_consistent = sum(1 for beam in supported_beams if beam.collapse_detected)
    ood_samples = [sample for sample in dataset if sample.get("input_mode", "").startswith("ood_")]
    rank_by_sample = {sample_id: sorted(ranks, key=lambda item: item.rerank_rank)[0] for sample_id, ranks in by_sample.items()}
    ood_rejected = sum(1 for sample in ood_samples if rank_by_sample.get(sample["sample_id"]) and rank_by_sample[sample["sample_id"]].rejected)
    ood_false_accept = len(ood_samples) - ood_rejected
    quadrant_counts = Counter(rank.quadrant for rank in rank_records)
    pruning_candidates = collect_pruning_candidates(rank_records, all_records)
    return {
        "generation": generation,
        "single_winner_sample_exact_match": round(single_winner_exact / total, 4),
        "reranked_sample_exact_match": round(reranked_exact / total, 4),
        "group_beam_exact_match": round(group_beam_exact / max(len(supported_beams), 1), 4),
        "group_beam_consistency": round(group_beam_consistent / max(len(supported_beams), 1), 4),
        "low_score_correct_count": quadrant_counts.get("low_score_correct", 0),
        "high_score_wrong_count": quadrant_counts.get("high_score_wrong", 0),
        "rerank_improvement_count": rerank_improvement,
        "rerank_regression_count": rerank_regression,
        "wrong_consistent_group_count": wrong_consistent,
        "pruning_candidate_count": len(pruning_candidates),
        "collapse_penalty_hits": sum(1 for record in all_records if record.fitness_report.components.get("collapse_penalty")),
        "ood_rejection_rate": round(ood_rejected / max(len(ood_samples), 1), 4),
        "ood_false_accept_rate": round(ood_false_accept / max(len(ood_samples), 1), 4),
        "candidate_quadrant_counts": dict(quadrant_counts),
        "low_score_correct_examples": [rank.to_dict() for rank in rank_records if rank.quadrant == "low_score_correct"][:5],
        "high_score_wrong_examples": [rank.to_dict() for rank in rank_records if rank.quadrant == "high_score_wrong"][:5],
        "wrong_consistent_group_examples": [beam.to_dict() for beam in beam_results if beam.collapse_detected][:5],
        "representative_group_beams": [beam.to_dict() for beam in beam_results[:8]],
    }


def _perfect_per_layer_metrics(winners: List[CandidateRecord], records_by_task: List[List[CandidateRecord]], dataset: List[Dict]) -> Dict[str, Dict]:
    totals = Counter()
    correct = Counter()
    missing = Counter()
    recall = Counter()
    for winner, records, task in zip(winners, records_by_task, dataset):
        winner_pairs = dict(decision_pairs(winner.genome.branch_path))
        candidate_pairs = [dict(decision_pairs(record.genome.branch_path)) for record in records]
        for layer, expected in task["target_branch_path"]:
            totals[layer] += 1
            if layer not in winner_pairs:
                missing[layer] += 1
            elif winner_pairs[layer] == expected:
                correct[layer] += 1
            if any(pairs.get(layer) == expected for pairs in candidate_pairs):
                recall[layer] += 1
    return {
        layer: {
            "accuracy": round(correct[layer] / max(total, 1), 4),
            "recall_at_k": round(recall[layer] / max(total, 1), 4),
            "missing_rate": round(missing[layer] / max(total, 1), 4),
            "correct_count": correct[layer],
            "total_count": total,
        }
        for layer, total in totals.items()
    }


def _metrics_for_generation(generation: int, winners: List[CandidateRecord], dataset: List[Dict]) -> Dict:
    total = max(len(winners), 1)
    missing_layers = 0
    true_missing_layers = 0
    early_reject_short_paths = 0
    correct_early_rejects = 0
    wrong_early_rejects = 0
    branch_exact = 0
    target_exact = 0
    output_match = 0
    unsupported_correct = 0
    compile_checked = 0
    compile_success = 0
    run_success = 0
    wrong_branches = Counter()
    reject_by_layer = Counter()
    per_layer_reject = Counter()
    per_layer_seen = Counter()
    per_layer_continue = Counter()
    confidence_margin_by_layer = Counter()
    fitness_values = []
    no_confidence_reject_count = 0
    correct_no_confidence_reject_count = 0
    wrong_no_confidence_reject_count = 0
    typed_reject_count = 0
    false_accept_unsupported_count = 0
    false_reject_supported_count = 0
    for record, task in zip(winners, dataset):
        fitness = record.fitness_report
        fitness_values.append(fitness.total_fitness)
        target_pairs = task["target_branch_path"]
        pred_pairs = decision_pairs(record.genome.branch_path)
        branch_exact += int(pred_pairs == target_pairs)
        target_exact += int(fitness.target_ir_exact_match)
        output_match += int(fitness.expected_output_match)
        unsupported_correct += int(fitness.unsupported_correct)
        short_path = len(pred_pairs) < len(target_pairs)
        is_early_reject = bool(record.genome.branch_path.reject_type)
        missing_layers += int(short_path)
        true_missing_layers += int(short_path and not is_early_reject)
        early_reject_short_paths += int(short_path and is_early_reject)
        correct_early_rejects += int(is_early_reject and not task["supported"])
        wrong_early_rejects += int(is_early_reject and task["supported"])
        if fitness.compile_success is not None:
            compile_checked += 1
            compile_success += int(fitness.compile_success)
            run_success += int(fitness.run_success)
        for target in target_pairs:
            if target not in pred_pairs:
                selected = next((pair[1] for pair in pred_pairs if pair[0] == target[0]), "<missing>")
                wrong_branches[f"{target[0]}:{target[1]} -> {selected}"] += 1
        if record.genome.branch_path.reject_type:
            reject_by_layer[record.genome.branch_path.rejected_by_layer or "<unknown>"] += 1
            if record.genome.branch_path.reject_type == "no_confident_branch":
                no_confidence_reject_count += 1
                correct_no_confidence_reject_count += int(not task["supported"])
                wrong_no_confidence_reject_count += int(task["supported"])
            if record.genome.branch_path.reject_type == "typed_rejection":
                typed_reject_count += 1
        false_accept_unsupported_count += int((not task["supported"]) and not record.phenotype.unsupported_pred)
        false_reject_supported_count += int(task["supported"] and record.phenotype.unsupported_pred)
        for decision in record.genome.branch_path.decisions:
            per_layer_seen[decision.layer_name] += 1
            confidence_margin_by_layer[decision.layer_name] += decision.confidence_margin or 0
            if decision.can_continue:
                per_layer_continue[decision.layer_name] += 1
            else:
                per_layer_reject[decision.layer_name] += 1
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
        "true_missing_layer_rate": round(true_missing_layers / total, 4),
        "early_reject_short_path_rate": round(early_reject_short_paths / total, 4),
        "correct_early_reject_rate": round(correct_early_rejects / total, 4),
        "wrong_early_reject_rate": round(wrong_early_rejects / total, 4),
        "most_common_wrong_branch_decisions": wrong_branches.most_common(10),
        "no_confidence_reject_count": no_confidence_reject_count,
        "correct_no_confidence_reject_count": correct_no_confidence_reject_count,
        "wrong_no_confidence_reject_count": wrong_no_confidence_reject_count,
        "typed_reject_count": typed_reject_count,
        "false_accept_unsupported_count": false_accept_unsupported_count,
        "false_reject_supported_count": false_reject_supported_count,
        "per_layer_reject_count": dict(per_layer_reject),
        "per_layer_continue_rate": {
            layer: round(per_layer_continue[layer] / max(count, 1), 4)
            for layer, count in per_layer_seen.items()
        },
        "rejected_by_layer_distribution": dict(reject_by_layer),
        "confidence_margin_by_layer": {
            layer: round(confidence_margin_by_layer[layer] / max(count, 1), 4)
            for layer, count in per_layer_seen.items()
        },
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


def _candidate_recall_metrics(records_by_task: List[List[CandidateRecord]], dataset: List[Dict], criteria) -> Dict:
    totals = Counter()
    winner_correct = Counter()
    recall_correct = Counter()
    false_reject = 0
    false_accept = 0
    true_supported_pred_supported = 0
    true_supported_pred_unsupported = 0
    true_unsupported_pred_supported = 0
    true_unsupported_pred_unsupported = 0
    for records, task in zip(records_by_task, dataset):
        winner = max(records, key=lambda rec: rec.fitness_report.total_fitness)
        winner_pairs = dict(decision_pairs(winner.genome.branch_path))
        candidate_pairs = [dict(decision_pairs(record.genome.branch_path)) for record in records]
        for layer, expected in task["target_branch_path"]:
            totals[layer] += 1
            winner_correct[layer] += int(winner_pairs.get(layer) == expected)
            recall_correct[layer] += int(any(pairs.get(layer) == expected for pairs in candidate_pairs))
        target_support = "supported" if task["supported"] else "unsupported"
        pred_support = winner_pairs.get("support_gate")
        if target_support == "supported" and pred_support == "supported":
            true_supported_pred_supported += 1
        elif target_support == "supported":
            true_supported_pred_unsupported += 1
            false_reject += 1
        elif pred_support == "supported":
            true_unsupported_pred_supported += 1
            false_accept += 1
        else:
            true_unsupported_pred_unsupported += 1
    winner_accuracy = {layer: round(winner_correct[layer] / max(total, 1), 4) for layer, total in totals.items()}
    recall_at_k = {layer: round(recall_correct[layer] / max(total, 1), 4) for layer, total in totals.items()}
    required = {
        layer: required_correct_count(total, criteria.get_start_threshold(layer))
        for layer, total in totals.items()
    }
    support_precision = true_supported_pred_supported / max(true_supported_pred_supported + true_unsupported_pred_supported, 1)
    support_recall = true_supported_pred_supported / max(true_supported_pred_supported + true_supported_pred_unsupported, 1)
    return {
        "per_layer_winner_accuracy": winner_accuracy,
        "per_layer_recall_at_k": recall_at_k,
        "per_layer_correct_count": dict(winner_correct),
        "per_layer_required_correct_count": required,
        "per_layer_total_count": dict(totals),
        "support_gate_confusion_matrix": {
            "true_supported_pred_supported": true_supported_pred_supported,
            "true_supported_pred_unsupported": true_supported_pred_unsupported,
            "true_unsupported_pred_supported": true_unsupported_pred_supported,
            "true_unsupported_pred_unsupported": true_unsupported_pred_unsupported,
        },
        "support_gate_precision": round(support_precision, 4),
        "support_gate_recall": round(support_recall, 4),
        "support_gate_false_reject_count": false_reject,
        "support_gate_false_accept_count": false_accept,
    }


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
