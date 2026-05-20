from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.beam_backtracking import WideBeamBacktrackingConfig, WideBeamBacktrackingSearch
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.layer_clone import LayerCloneConfig, clone_layer_population, promote_clone_to_layer
from jianmu.self_learning.darwinforge.path_diagnostics import diagnose_paths
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


@dataclass
class WideBeamBacktrackingTrainerConfig:
    mode: str = "medium"
    population_per_layer: int = 32
    generations: int = 12
    beam_size: int = 32
    proposals_per_layer: int = 8
    exploration_quota: int = 2
    stochastic_samples_per_layer: int = 4
    confidence_noise: float = 3.0
    max_complete_paths: int = 128
    clone_count_per_layer: int = 4
    perturbation_scale: float = 0.15
    backtracking_window: int = 1
    backtracking_patience: int = 3
    max_backtracking_attempts: int = 3
    seed: int = 42
    train_limit: Optional[int] = 1200
    eval_limit: Optional[int] = 400
    ood_limit: Optional[int] = 200
    canonicalization_enabled: bool = True

    @classmethod
    def for_mode(cls, mode: str, **overrides):
        defaults = {
            "quick": dict(population_per_layer=16, generations=5, beam_size=16, proposals_per_layer=4, exploration_quota=1, stochastic_samples_per_layer=2, max_complete_paths=64, clone_count_per_layer=2, perturbation_scale=0.10, backtracking_window=1, backtracking_patience=2, train_limit=400, eval_limit=200, ood_limit=100),
            "medium": dict(population_per_layer=32, generations=12, beam_size=32, proposals_per_layer=8, exploration_quota=2, stochastic_samples_per_layer=4, max_complete_paths=128, clone_count_per_layer=4, perturbation_scale=0.15, backtracking_window=1, backtracking_patience=3, train_limit=1200, eval_limit=400, ood_limit=200),
            "full": dict(population_per_layer=64, generations=30, beam_size=64, proposals_per_layer=12, exploration_quota=4, stochastic_samples_per_layer=8, max_complete_paths=256, clone_count_per_layer=6, perturbation_scale=0.20, backtracking_window=2, backtracking_patience=4, train_limit=None, eval_limit=None, ood_limit=None),
        }[mode]
        payload = {"mode": mode, **defaults, **{key: value for key, value in overrides.items() if value is not None}}
        return cls(**payload)

    def to_search_config(self):
        return WideBeamBacktrackingConfig(
            beam_size=self.beam_size,
            proposals_per_layer=self.proposals_per_layer,
            exploration_quota=self.exploration_quota,
            stochastic_samples_per_layer=self.stochastic_samples_per_layer,
            confidence_noise=self.confidence_noise,
            max_complete_paths=self.max_complete_paths,
            clone_count_per_layer=self.clone_count_per_layer,
            perturbation_scale=self.perturbation_scale,
            backtracking_window=self.backtracking_window,
            backtracking_patience=self.backtracking_patience,
            max_backtracking_attempts=self.max_backtracking_attempts,
            seed=self.seed,
            canonicalization_enabled=self.canonicalization_enabled,
        )

    def to_dict(self):
        return dict(self.__dict__)


class WideBeamBacktrackingTrainer:
    """Wide-Beam Backtracking Search（宽束回溯搜索） trainer scaffold."""

    def __init__(self, train_samples: List[Dict], eval_samples: List[Dict], ood_samples: List[Dict], config: WideBeamBacktrackingTrainerConfig):
        self.config = config
        self.train_samples = train_samples[: config.train_limit] if config.train_limit else train_samples
        self.eval_samples = eval_samples[: config.eval_limit] if config.eval_limit else eval_samples
        self.ood_samples = ood_samples[: config.ood_limit] if config.ood_limit else ood_samples
        self.population = LayerPreservedPopulation.initialize(population_per_layer=config.population_per_layer, seed=config.seed)
        self.search = WideBeamBacktrackingSearch(config.to_search_config())
        self.synthesis = AtomicSynthesis()
        self.curve: List[Dict] = []
        self.diagnostics: List[Dict] = []
        self.candidates: List[Dict] = []
        self.clone_events: List[Dict] = []
        self.active_clones: Dict[str, List] = {}
        self.backtracking_attempts = Counter()

    def train(self):
        started = time.time()
        for generation in range(self.config.generations):
            if generation and generation % self.config.backtracking_patience == 0:
                self._start_backtracking(generation)
            records, diagnostics = self._run_samples(self.train_samples, generation, training=True)
            self._promote_or_discard_clones(generation, diagnostics)
            self.population.evolve(self._selected_records(records))
            row = _aggregate_diagnostics(diagnostics)
            row.update({"generation": generation, "record_count": len(records)})
            self.curve.append(row)
        eval_records, eval_diags = self._run_samples(self.eval_samples + self.ood_samples, self.config.generations, training=False)
        metrics = _aggregate_diagnostics(eval_diags)
        metrics.update(
            {
                "config": self.config.to_dict(),
                "train_sample_count": len(self.train_samples),
                "eval_sample_count": len(self.eval_samples),
                "ood_sample_count": len(self.ood_samples),
                "runtime_seconds": round(time.time() - started, 4),
                "curve": self.curve,
                "diagnostics": eval_diags,
                "candidate_rows": self.candidates[:5000],
                "clone_events": self.clone_events,
                "by_input_mode": _group_diag(eval_diags, "input_mode"),
                "by_structure_policy": _group_diag(eval_diags, "structure_policy"),
                "failure_examples": _failure_examples(eval_diags),
                "clone_promotion_count": sum(1 for event in self.clone_events if event.get("event") == "promoted"),
                "clone_discard_count": sum(1 for event in self.clone_events if event.get("event") == "discarded"),
                "backtracking_event_count": sum(1 for event in self.clone_events if event.get("event") == "created"),
            }
        )
        return metrics

    def _run_samples(self, samples, generation, training: bool):
        all_records = []
        diagnostics = []
        for sample in samples:
            features = build_training_features(sample["input_text"], self.config.canonicalization_enabled)
            genomes = self.search.generate_paths(self.population, features, active_clones=self.active_clones, generation=generation)
            records = []
            for genome in genomes:
                phenotype = self.synthesis.synthesize(genome, features)
                fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
                self._shape_reward(fitness, sample, phenotype)
                record = CandidateRecord(genome, phenotype, fitness)
                records.append(record)
            diag = diagnose_paths(sample, records, canonical_text=features.get("canonical_text", sample["input_text"]))
            diag_dict = diag.to_dict()
            diag_dict["input_mode"] = sample.get("input_mode")
            diag_dict["structure_policy"] = sample.get("structure_policy")
            diagnostics.append(diag_dict)
            all_records.extend(records)
            if training and len(self.candidates) < 5000:
                self.candidates.extend(_candidate_rows(sample, records[: min(len(records), 5)], generation, features.get("canonical_text", "")))
        self.diagnostics.extend(diagnostics[:2000])
        return all_records, diagnostics

    def _shape_reward(self, fitness, sample, phenotype):
        if sample.get("supported") and fitness.target_ir_exact_match:
            fitness.total_fitness += 4.0
        if sample.get("supported") and fitness.expected_output_match:
            fitness.total_fitness += 2.0
        if sample.get("supported") and phenotype.unsupported_pred:
            fitness.total_fitness -= 4.0
        if (not sample.get("supported")) and not phenotype.unsupported_pred:
            fitness.total_fitness -= 5.0
        if (not sample.get("supported")) and phenotype.unsupported_pred:
            fitness.total_fitness += 2.0

    def _selected_records(self, records):
        ranked = sorted(records, key=lambda record: record.fitness_report.total_fitness, reverse=True)
        return ranked[: max(self.config.beam_size, 1)]

    def _start_backtracking(self, generation):
        distribution = Counter(row.get("dominant_first_wrong_layer") for row in self.curve[-self.config.backtracking_patience :] if row.get("dominant_first_wrong_layer"))
        layer = distribution.most_common(1)[0][0] if distribution else "arithmetic_family"
        layer_names = [name for name, _ in LAYER_DEFINITIONS]
        if layer not in layer_names:
            layer = "arithmetic_family"
        index = layer_names.index(layer)
        start = max(0, index - self.config.backtracking_window)
        layers = layer_names[start : index + 1]
        clone_config = LayerCloneConfig(
            clone_count_per_layer=self.config.clone_count_per_layer,
            perturbation_scale=self.config.perturbation_scale,
            seed=self.config.seed,
        )
        for layer_name in layers:
            if self.backtracking_attempts[layer_name] >= self.config.max_backtracking_attempts:
                continue
            clones = clone_layer_population(self.population.per_layer[layer_name], layer_name, clone_config, generation)
            self.active_clones[layer_name] = clones
            self.backtracking_attempts[layer_name] += 1
            for clone in clones:
                self.clone_events.append({"event": "created", "generation": generation, "layer_name": layer_name, **clone.to_dict()})

    def _promote_or_discard_clones(self, generation, diagnostics):
        if not self.active_clones:
            return
        clone_hits = Counter()
        for row in diagnostics:
            if row.get("correct_targetir_in_beam"):
                for clone_id in row.get("source_clone_ids_used", []):
                    if clone_id != "base":
                        clone_hits[clone_id] += 1
        total = max(len(diagnostics), 1)
        for layer_name, clones in list(self.active_clones.items()):
            kept = []
            for clone in clones:
                clone_metric = clone_hits[clone.clone_id] / total
                promoted = promote_clone_to_layer(self.population, clone, layer_name, base_metric=0.0, clone_metric=clone_metric, promote_margin=0.01)
                self.clone_events.append({"event": "promoted" if promoted else "discarded", "generation": generation, "layer_name": layer_name, "clone_id": clone.clone_id, "clone_metric": round(clone_metric, 4)})
                if not promoted:
                    kept.append(clone)
            self.active_clones[layer_name] = kept[:2]


def write_wide_beam_outputs(metrics: Dict, records_dir: Path) -> Dict[str, str]:
    records_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics_path": records_dir / "wide_beam_backtracking_metrics.json",
        "report_path": records_dir / "wide_beam_backtracking_report.md",
        "diagnostics_path": records_dir / "wide_beam_backtracking_diagnostics.jsonl",
        "candidates_path": records_dir / "wide_beam_backtracking_candidates.jsonl",
        "curve_path": records_dir / "wide_beam_backtracking_curve.jsonl",
        "clone_events_path": records_dir / "wide_beam_backtracking_clone_events.jsonl",
        "failure_examples_path": records_dir / "wide_beam_backtracking_failure_examples.json",
    }
    serializable = {k: v for k, v in metrics.items() if k not in {"diagnostics", "candidate_rows", "curve", "clone_events", "failure_examples"}}
    paths["metrics_path"].write_text(json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    paths["diagnostics_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["diagnostics"]), encoding="utf-8")
    paths["candidates_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["candidate_rows"]), encoding="utf-8")
    paths["curve_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["curve"]), encoding="utf-8")
    paths["clone_events_path"].write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["clone_events"]), encoding="utf-8")
    paths["failure_examples_path"].write_text(json.dumps(metrics["failure_examples"], ensure_ascii=False, indent=2), encoding="utf-8")
    paths["report_path"].write_text(_report(metrics), encoding="utf-8")
    return {key: str(value) for key, value in paths.items()}


def _aggregate_diagnostics(rows: List[Dict]) -> Dict:
    supported = [row for row in rows if row.get("supported")]
    unsupported = [row for row in rows if not row.get("supported")]
    first_wrong = Counter(row.get("first_wrong_layer") for row in rows if row.get("first_wrong_layer"))
    rejected = Counter(row.get("rejected_by_layer") for row in rows if row.get("rejected_by_layer"))
    ranks = [row["correct_targetir_rank"] for row in rows if row.get("correct_targetir_rank")]
    zh = [row for row in supported if row.get("input_mode") == "zh_number_expression"]
    parentheses = [row for row in supported if row.get("structure_policy") == "parenthesized_tree"]
    mixed = [row for row in supported if row.get("structure_policy") == "precedence_tree"]
    division = [row for row in supported if "div(" in str(row.get("target_ir_true"))]
    unsupported_arithmetic = [row for row in rows if row.get("input_mode") == "unsupported_arithmetic"]
    false_accept_unsupported_rate = _rate(unsupported, lambda row: not row.get("rejected_by_layer"))
    return {
        "sample_count": len(rows),
        "target_ir_exact_match_top1": _rate(supported, "top1_exact"),
        "target_ir_exact_match_beam_oracle": _rate(supported, "best_beam_exact"),
        "beam_oracle_gap": round(_rate(supported, "best_beam_exact") - _rate(supported, "top1_exact"), 4),
        "correct_targetir_in_beam_rate": _rate(supported, "correct_targetir_in_beam"),
        "correct_path_in_beam_rate": _rate(supported, "correct_path_in_beam"),
        "top1_wrong_but_correct_in_beam_rate": _rate(supported, "top1_wrong_but_correct_in_beam"),
        "candidate_space_failure_rate": _rate(supported, "candidate_space_failure"),
        "ranking_failure_rate": _rate(supported, "ranking_failure"),
        "upstream_boundary_failure_rate": _rate(supported, "upstream_boundary_failure"),
        "synthesis_failure_rate": _rate(supported, "synthesis_failure"),
        "average_correct_targetir_rank": round(sum(ranks) / max(len(ranks), 1), 4),
        "average_path_count": round(sum(row.get("path_count", 0) for row in rows) / max(len(rows), 1), 4),
        "complete_path_rate": round(sum(row.get("complete_path_count", 0) for row in rows) / max(sum(row.get("path_count", 0) for row in rows), 1), 4),
        "false_reject_supported_rate": _rate(supported, lambda row: row.get("rejected_by_layer") is not None),
        "false_accept_unsupported_rate": false_accept_unsupported_rate,
        "ood_false_accept_rate": false_accept_unsupported_rate,
        "ood_rejection_rate": _rate(unsupported, lambda row: row.get("rejected_by_layer") is not None),
        "zh_number_top1_exact": _rate(zh, "top1_exact"),
        "zh_number_beam_oracle_exact": _rate(zh, "best_beam_exact"),
        "zh_number_correct_targetir_in_beam_rate": _rate(zh, "correct_targetir_in_beam"),
        "parentheses_correct_targetir_in_beam_rate": _rate(parentheses, "correct_targetir_in_beam"),
        "mixed_precedence_correct_targetir_in_beam_rate": _rate(mixed, "correct_targetir_in_beam"),
        "exact_division_correct_targetir_in_beam_rate": _rate(division, "correct_targetir_in_beam"),
        "unsupported_arithmetic_false_accept_rate": _rate(unsupported_arithmetic, lambda row: not row.get("rejected_by_layer")),
        "first_wrong_layer_distribution": dict(first_wrong),
        "rejected_by_layer_distribution": dict(rejected),
        "dominant_first_wrong_layer": first_wrong.most_common(1)[0][0] if first_wrong else None,
    }


def _group_diag(rows, key):
    buckets = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key))].append(row)
    return {name: _aggregate_diagnostics(bucket) for name, bucket in sorted(buckets.items())}


def _candidate_rows(sample, records, generation, canonical_text):
    rows = []
    for rank, record in enumerate(records, start=1):
        rows.append(
            {
                "generation": generation,
                "rank": rank,
                "sample_id": sample.get("sample_id"),
                "raw_text": sample.get("input_text"),
                "canonical_text": canonical_text,
                "target_ir_true": sample.get("target_ir_canonical"),
                "target_ir_pred": record.phenotype.target_ir_canonical,
                "fitness": record.fitness_report.total_fitness,
                "decisions": [[d.layer_name, d.selected, d.evidence.get("source_clone_id", "base")] for d in record.genome.branch_path.decisions],
            }
        )
    return rows


def _failure_examples(rows):
    examples = {}
    for key in ["ranking_failure", "candidate_space_failure", "upstream_boundary_failure", "synthesis_failure"]:
        examples[key] = [row for row in rows if row.get(key)][:5]
    return examples


def _rate(rows, key) -> float:
    if not rows:
        return 0.0
    if callable(key):
        return round(sum(1 for row in rows if key(row)) / len(rows), 4)
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)


def _report(metrics):
    config = metrics["config"]
    lines = [
        "# Wide-Beam Backtracking Search（宽束回溯搜索） Report",
        "",
        "## Config（配置）",
        f"- mode: {config['mode']}",
        f"- bounded_runtime_override（有界运行覆盖）: {metrics.get('bounded_runtime_override', False)}",
        f"- Branch Beam Size（分支束宽）: {config['beam_size']}",
        f"- proposals_per_layer（每层候选数）: {config['proposals_per_layer']}",
        f"- stochastic_samples_per_layer（每层随机采样数）: {config['stochastic_samples_per_layer']}",
        f"- confidence_noise（置信噪声）: {config['confidence_noise']}",
        f"- clone_count_per_layer（每层克隆数）: {config['clone_count_per_layer']}",
        f"- perturbation_scale（扰动尺度）: {config['perturbation_scale']}",
        f"- Backtracking Window（回溯窗口）: {config['backtracking_window']}",
        f"- backtracking_patience（回溯耐心）: {config['backtracking_patience']}",
        f"- population_per_layer（每层种群数量）: {config['population_per_layer']}",
        f"- generations（训练代数）: {config['generations']}",
        f"- train/eval/ood: {metrics['train_sample_count']} / {metrics['eval_sample_count']} / {metrics['ood_sample_count']}",
        "",
        "## Full Path Diagnostics（完整路径诊断）",
        f"- target_ir_exact_match_top1（Top1 TargetIR 精确匹配）: {metrics['target_ir_exact_match_top1']}",
        f"- target_ir_exact_match_beam_oracle（束内 Oracle TargetIR 精确匹配）: {metrics['target_ir_exact_match_beam_oracle']}",
        f"- beam_oracle_gap（束内上限差距）: {metrics['beam_oracle_gap']}",
        f"- correct_targetir_in_beam_rate（正确 TargetIR 在束内率）: {metrics['correct_targetir_in_beam_rate']}",
        f"- candidate_space_failure_rate（候选空间失败率）: {metrics['candidate_space_failure_rate']}",
        f"- ranking_failure_rate（排序失败率）: {metrics['ranking_failure_rate']}",
        f"- upstream_boundary_failure_rate（上游边界失败率）: {metrics['upstream_boundary_failure_rate']}",
        f"- synthesis_failure_rate（合成失败率）: {metrics['synthesis_failure_rate']}",
        f"- first_wrong_layer_distribution（首个错误层分布）: {metrics['first_wrong_layer_distribution']}",
        f"- rejected_by_layer_distribution（拒绝层分布）: {metrics['rejected_by_layer_distribution']}",
        "",
        "## Clone and Backtracking（克隆与回溯）",
        f"- clone_promotion_count（克隆提升数）: {metrics.get('clone_promotion_count', 0)}",
        f"- clone_discard_count（克隆丢弃数）: {metrics.get('clone_discard_count', 0)}",
        f"- backtracking_event_count（回溯事件数）: {metrics.get('backtracking_event_count', 0)}",
        "",
        "## Non-Claims（非主张）",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        "- This is a Wide-Beam Backtracking Search（宽束回溯搜索） diagnostic and training scaffold.",
    ]
    return "\n".join(lines) + "\n"
