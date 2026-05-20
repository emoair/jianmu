from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.darwinforge.annealed_pruning import annealing_schedule
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.beam_backtracking import WideBeamBacktrackingConfig, WideBeamBacktrackingSearch
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.root_necrosis import NecrosisQueue, summarize_necrosis
from jianmu.self_learning.darwinforge.root_regrowth import plan_regrowth, summarize_regrowth
from jianmu.self_learning.darwinforge.root_viability import diagnose_root_viability, summarize_viability
from jianmu.self_learning.darwinforge.rootforge import nutrient_contrast, root_candidate_from_record
from jianmu.self_learning.darwinforge.path_diagnostics import diagnose_paths
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


@dataclass
class RootForgeGrowthConfig:
    mode: str = "quick"
    train_limit: int = 300
    eval_limit: int = 150
    ood_limit: int = 100
    generations: int = 5
    beam_size: int = 24
    proposals_per_layer: int = 6
    stochastic_samples_per_layer: int = 3
    clone_count_per_layer: int = 2
    perturbation_scale: float = 0.15
    population_per_layer: int = 24
    seed: int = 42
    canonicalization_enabled: bool = True

    @classmethod
    def for_mode(cls, mode: str, **overrides):
        defaults = {
            "quick": dict(train_limit=300, eval_limit=150, ood_limit=100, generations=5, beam_size=24, clone_count_per_layer=2, perturbation_scale=0.15, population_per_layer=24),
            "medium": dict(train_limit=1000, eval_limit=400, ood_limit=200, generations=12, beam_size=48, clone_count_per_layer=4, perturbation_scale=0.15, population_per_layer=32),
        }[mode]
        payload = {"mode": mode, **defaults, **{key: value for key, value in overrides.items() if value is not None}}
        return cls(**payload)

    def to_search_config(self, annealing_state=None):
        beam_size = annealing_state.effective_beam_size if annealing_state else self.beam_size
        return WideBeamBacktrackingConfig(
            beam_size=beam_size,
            proposals_per_layer=self.proposals_per_layer,
            stochastic_samples_per_layer=self.stochastic_samples_per_layer,
            clone_count_per_layer=self.clone_count_per_layer,
            perturbation_scale=self.perturbation_scale,
            max_complete_paths=max(beam_size * 4, 32),
            seed=self.seed,
            canonicalization_enabled=self.canonicalization_enabled,
        )

    def to_dict(self):
        return dict(self.__dict__)


class RootForgeGrowthTrainer:
    def __init__(self, train_samples: List[Dict], eval_samples: List[Dict], ood_samples: List[Dict], config: RootForgeGrowthConfig):
        self.config = config
        self.train_samples = train_samples[: config.train_limit]
        self.eval_samples = eval_samples[: config.eval_limit]
        self.ood_samples = ood_samples[: config.ood_limit]
        self.population = LayerPreservedPopulation.initialize(population_per_layer=config.population_per_layer, seed=config.seed)
        self.synthesis = AtomicSynthesis()
        self.curve: List[Dict] = []
        self.candidate_rows: List[Dict] = []
        self.viability_rows: List[Dict] = []
        self.regrowth_events = []
        self.necrosis_queue = NecrosisQueue()
        self.annealing_rows: List[Dict] = []
        self.contrast_events: List[Dict] = []
        self.artifact_suffix_stripped_count = 0
        self.action_counts = Counter()

    def train(self) -> Dict:
        started = time.time()
        for generation in range(self.config.generations):
            annealing = annealing_schedule(generation, self.config.generations, self.config.beam_size, self.config.perturbation_scale)
            self.annealing_rows.append(annealing.to_dict())
            search = WideBeamBacktrackingSearch(self.config.to_search_config(annealing))
            records_for_evolution = []
            generation_diags = []
            for sample in self.train_samples:
                records, diag = self._run_sample(sample, search, generation)
                generation_diags.append(diag)
                roots = self._roots_for_sample(sample, records, diag)
                records_for_evolution.extend(self._select_records(records, roots))
                self._process_roots(roots, generation, annealing.annealing_phase, split="train")
            self.population.evolve(records_for_evolution)
            row = _aggregate_diagnostics(generation_diags)
            row.update({"generation": generation, "annealing_phase": annealing.annealing_phase})
            self.curve.append(row)
        eval_diags = []
        for sample in self.eval_samples + self.ood_samples:
            records, diag = self._run_sample(sample, WideBeamBacktrackingSearch(self.config.to_search_config()), self.config.generations)
            eval_diags.append(diag)
            self._roots_for_sample(sample, records, diag, keep_candidates=True)
        train_low = sum(1 for row in self.viability_rows if row.get("split") == "train")
        eval_low = sum(1 for row in self.candidate_rows if row.get("split") == "eval" and row.get("root_type") == "low_score_correct")
        metrics = _aggregate_diagnostics(eval_diags)
        metrics.update(_repair_metrics(eval_diags))
        metrics.update(summarize_viability([_report_from_dict(row) for row in self.viability_rows]))
        metrics.update(summarize_regrowth([_event_from_dict(row) for row in self.regrowth_events]))
        metrics.update(summarize_necrosis(self.necrosis_queue.events))
        metrics.update(
            {
                "config": self.config.to_dict(),
                "train_sample_count": len(self.train_samples),
                "eval_sample_count": len(self.eval_samples),
                "ood_sample_count": len(self.ood_samples),
                "runtime_seconds": round(time.time() - started, 4),
                "artifact_suffix_stripped_count": self.artifact_suffix_stripped_count,
                "train_low_score_correct_count": train_low,
                "eval_low_score_correct_count": eval_low,
                "low_score_correct_without_action_count": self.action_counts["low_score_correct_without_action"],
                "regrowth_queue_added_count": self.action_counts["regrowth_queue_added"],
                "stable_root_buffer_added_count": self.action_counts["stable_root_buffer_added"],
                "necrosis_queue_added_count": self.action_counts["necrosis_queue_added"],
                "nutrient_contrast_event_count": len(self.contrast_events),
                "positive_negative_margin_avg": _avg([event["positive_score"] - event["negative_score"] for event in self.contrast_events]),
                "annealing_phases_completed": sorted({row["annealing_phase"] for row in self.annealing_rows}),
                "curve": self.curve,
                "candidates": self.candidate_rows[:5000],
                "viability": self.viability_rows,
                "regrowth_events": self.regrowth_events,
                "necrosis_events": [event.to_dict() for event in self.necrosis_queue.events],
                "annealing": self.annealing_rows,
                "failure_examples": _failure_examples(eval_diags),
                "eval_diagnostics": eval_diags,
                "by_input_mode": _group_diag(eval_diags, "input_mode"),
                "by_structure_policy": _group_diag(eval_diags, "structure_policy"),
            }
        )
        return metrics

    def _run_sample(self, sample: Dict, search: WideBeamBacktrackingSearch, generation: int):
        canonical = canonicalize_symbols(sample["input_text"])
        if "stripped_dataset_artifact_suffix" in canonical.warnings:
            self.artifact_suffix_stripped_count += 1
        features = build_training_features(sample["input_text"], self.config.canonicalization_enabled)
        genomes = search.generate_paths(self.population, features, generation=generation)
        records = []
        for genome in genomes:
            phenotype = self.synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
            record = CandidateRecord(genome, phenotype, fitness)
            records.append(record)
        diag = diagnose_paths(sample, records, canonical_text=features.get("canonical_text", canonical.canonical_text)).to_dict()
        diag["input_mode"] = sample.get("input_mode")
        diag["structure_policy"] = sample.get("structure_policy")
        diag["expression_family"] = sample.get("expression_family")
        diag["unsupported_reason"] = sample.get("unsupported_reason")
        return records, diag

    def _roots_for_sample(self, sample, records, diag, keep_candidates=False):
        ranked = sorted(records, key=lambda record: record.fitness_report.total_fitness, reverse=True)
        roots = []
        canonical_text = diag.get("canonical_text", sample["input_text"])
        for rank, record in enumerate(ranked[: min(len(ranked), 8)], start=1):
            root = root_candidate_from_record(sample, record, rank, canonical_text, diag)
            roots.append(root)
            if keep_candidates or len(self.candidate_rows) < 5000:
                row = root.to_dict()
                row["target_ir_true"] = sample.get("target_ir_canonical")
                row["split"] = sample.get("split", "train")
                self.candidate_rows.append(row)
        return roots

    def _process_roots(self, roots, generation, phase, split: str):
        positives = [root for root in roots if root.target_ir_exact_match or root.unsupported_correct]
        negatives = [root for root in roots if root.root_type == "high_score_wrong" or (root.nutrient_score <= 0 and not root.target_ir_exact_match)]
        for root in roots:
            if root.root_type == "low_score_correct":
                report = diagnose_root_viability(root, perturbation_reproduction_rate=0.6 if len(root.stable_prefix) >= 4 else 0.2)
                report_row = report.to_dict()
                report_row.update(
                    {
                        "split": split,
                        "generation": generation,
                        "sample_id": root.sample_id,
                        "target_ir_exact_match": root.target_ir_exact_match,
                        "beam_eval_scope": split,
                    }
                )
                self.viability_rows.append(report_row)
                acted = False
                if report.classification in {"undervalued_correct_root", "alternative_valid_root"}:
                    self.action_counts["stable_root_buffer_added"] += 1
                    acted = True
                    if root.rank > 3 or root.nutrient_score < 4.0:
                        event = plan_regrowth(root, generation, [name for name, _ in LAYER_DEFINITIONS], window=1, reason=report.classification)
                        self.regrowth_events.append(event.to_dict())
                        self.action_counts["regrowth_queue_added"] += 1
                elif report.classification == "lucky_correct_root":
                    event = plan_regrowth(root, generation, [name for name, _ in LAYER_DEFINITIONS], window=1)
                    self.regrowth_events.append(event.to_dict())
                    self.action_counts["regrowth_queue_added"] += 1
                    acted = True
                elif report.classification == "unstable_correct_root":
                    self.necrosis_queue.observe(root, generation, phase=phase)
                    self.action_counts["necrosis_queue_added"] += 1
                    acted = True
                if not acted:
                    self.action_counts["low_score_correct_without_action"] += 1
            if root.root_type == "high_score_wrong" or root.nutrient_score <= 0:
                self.necrosis_queue.observe(root, generation, phase=phase)
        if positives and negatives:
            event = nutrient_contrast(positives[0], negatives[0])
            self.contrast_events.append(event)

    def _select_records(self, records, roots):
        by_id = {root.root_id.split(":", 1)[1].rsplit(":", 1)[0]: root for root in roots}
        ranked = sorted(records, key=lambda record: record.fitness_report.total_fitness, reverse=True)
        selected = ranked[: max(4, self.config.beam_size // 2)]
        for record in ranked:
            if record.fitness_report.target_ir_exact_match and record not in selected:
                selected.append(record)
        return selected[: self.config.beam_size]


def write_rootforge_outputs(metrics: Dict, records_dir: Path) -> Dict[str, str]:
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "rootforge_metrics.json",
        "report_path": records_dir / "rootforge_report.md",
        "curve_path": records_dir / "rootforge_curve.jsonl",
        "candidates_path": records_dir / "rootforge_candidates.jsonl",
        "viability_path": records_dir / "rootforge_viability.jsonl",
        "regrowth_events_path": records_dir / "rootforge_regrowth_events.jsonl",
        "necrosis_events_path": records_dir / "rootforge_necrosis_events.jsonl",
        "annealing_path": records_dir / "rootforge_annealing.jsonl",
        "failure_examples_path": records_dir / "rootforge_failure_examples.json",
    }
    compact = {key: value for key, value in metrics.items() if key not in {"curve", "candidates", "viability", "regrowth_events", "necrosis_events", "annealing", "failure_examples", "eval_diagnostics"}}
    paths["metrics_path"].write_text(json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["curve_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["curve"]), encoding="utf-8")
    paths["candidates_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["candidates"]), encoding="utf-8")
    paths["viability_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["viability"]), encoding="utf-8")
    paths["regrowth_events_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["regrowth_events"]), encoding="utf-8")
    paths["necrosis_events_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["necrosis_events"]), encoding="utf-8")
    paths["annealing_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["annealing"]), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(metrics["failure_examples"], ensure_ascii=False, indent=2), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    return {key: str(path) for key, path in paths.items()}


def _aggregate_diagnostics(rows: List[Dict]) -> Dict:
    supported = [row for row in rows if row.get("supported")]
    unsupported = [row for row in rows if not row.get("supported")]
    first_wrong = Counter(row.get("first_wrong_layer") for row in rows if row.get("first_wrong_layer"))
    return {
        "sample_count": len(rows),
        "target_ir_exact_match_top1": _rate(supported, "top1_exact"),
        "target_ir_exact_match_beam_oracle": _rate(supported, "best_beam_exact"),
        "correct_targetir_in_beam_rate": _rate(supported, "correct_targetir_in_beam"),
        "candidate_space_failure_rate": _rate(supported, "candidate_space_failure"),
        "ranking_failure_rate": _rate(supported, "ranking_failure"),
        "ood_rejection_rate": _rate(unsupported, lambda row: row.get("rejected_by_layer") is not None),
        "ood_false_accept_rate": _rate(unsupported, lambda row: row.get("rejected_by_layer") is None),
        "first_wrong_layer_distribution": dict(first_wrong),
    }


def _repair_metrics(rows: List[Dict]) -> Dict:
    literal = [row for row in rows if row.get("structure_policy") == "literal_value" and row.get("supported")]
    div_add = [row for row in rows if row.get("target_ir_true") and "add(div(" in row.get("target_ir_true")]
    return {
        "literal_only_targetir_exact_match": _rate(literal, "top1_exact"),
        "precedence_div_add_success_rate": _rate(div_add, "top1_exact"),
    }


def _group_diag(rows, key):
    buckets = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key))].append(row)
    return {name: _aggregate_diagnostics(bucket) for name, bucket in sorted(buckets.items())}


def _failure_examples(rows):
    return {
        "candidate_space_failure": [row for row in rows if row.get("candidate_space_failure")][:5],
        "ranking_failure": [row for row in rows if row.get("ranking_failure")][:5],
    }


def _rate(rows, key) -> float:
    if not rows:
        return 0.0
    if callable(key):
        return round(sum(1 for row in rows if key(row)) / len(rows), 4)
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)


def _avg(values) -> float:
    return round(sum(values) / max(len(values), 1), 4)


def _report_from_dict(row):
    return type("ViabilityLike", (), row)


def _event_from_dict(row):
    return type("EventLike", (), row)


def _report(metrics):
    lines = [
        "# RootForge Growth Dynamics（根铸生长动力学） Report",
        "",
        "## Candidate Space Repair（候选空间修复）",
        f"- literal_only_targetir_exact_match（字面量目标中间表示精确匹配）: {metrics.get('literal_only_targetir_exact_match', 0.0)}",
        f"- precedence_div_add_success_rate（除法再加优先级成功率）: {metrics.get('precedence_div_add_success_rate', 0.0)}",
        f"- artifact_suffix_stripped_count（伪影后缀剥离数）: {metrics.get('artifact_suffix_stripped_count', 0)}",
        "",
        "## Path Metrics（路径指标）",
        f"- target_ir_exact_match_top1（Top1 目标中间表示精确匹配）: {metrics.get('target_ir_exact_match_top1', 0.0)}",
        f"- target_ir_exact_match_beam_oracle（束内目标中间表示上限）: {metrics.get('target_ir_exact_match_beam_oracle', 0.0)}",
        f"- correct_targetir_in_beam_rate（正确目标中间表示在束内率）: {metrics.get('correct_targetir_in_beam_rate', 0.0)}",
        f"- candidate_space_failure_rate（候选空间失败率）: {metrics.get('candidate_space_failure_rate', 0.0)}",
        f"- ranking_failure_rate（排序失败率）: {metrics.get('ranking_failure_rate', 0.0)}",
        f"- first_wrong_layer_distribution（首个错误层分布）: {metrics.get('first_wrong_layer_distribution', {})}",
        "",
        "## RootForge（根铸） Dynamics",
        f"- low_score_correct_count（低分正确根数量）: {metrics.get('low_score_correct_count', 0)}",
        f"- undervalued_correct_count（被低估正确根数量）: {metrics.get('undervalued_correct_count', 0)}",
        f"- lucky_correct_count（幸运正确根数量）: {metrics.get('lucky_correct_count', 0)}",
        f"- regrowth_event_count（再生事件数量）: {metrics.get('regrowth_event_count', 0)}",
        f"- regrowth_success_count（再生成功数量）: {metrics.get('regrowth_success_count', 0)}",
        f"- necrosis_candidate_count（坏死候选数量）: {metrics.get('necrosis_candidate_count', 0)}",
        f"- necrosis_pruned_count（坏死剪枝数量）: {metrics.get('necrosis_pruned_count', 0)}",
        f"- nutrient_contrast_event_count（养分对比事件数量）: {metrics.get('nutrient_contrast_event_count', 0)}",
        f"- annealing_phases_completed（已完成退火阶段）: {metrics.get('annealing_phases_completed', [])}",
        "",
        "## OOD Evaluation（分布外评测）",
        f"- ood_rejection_rate（分布外拒绝率）: {metrics.get('ood_rejection_rate', 0.0)}",
        f"- ood_false_accept_rate（分布外误接收率）: {metrics.get('ood_false_accept_rate', 0.0)}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This is a RootForge Growth Dynamics（根铸生长动力学） scaffold, not a release claim.",
    ]
    return "\n".join(lines) + "\n"
