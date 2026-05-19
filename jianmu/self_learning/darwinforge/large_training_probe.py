import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.stratified_eval import evaluate_dataset_stratified


@dataclass
class ProbeConfig:
    mode: str = "medium"
    population_per_layer: int = 32
    generations: int = 20
    top_k: int = 5
    seed: int = 42
    train_sample_limit: Optional[int] = 2400
    eval_sample_limit: Optional[int] = 1200
    checkpoint_every: int = 5

    @classmethod
    def for_mode(cls, mode: str, **overrides) -> "ProbeConfig":
        defaults = {
            "quick": dict(population_per_layer=16, generations=5, top_k=3, train_sample_limit=800, eval_sample_limit=400),
            "medium": dict(population_per_layer=32, generations=20, top_k=5, train_sample_limit=2400, eval_sample_limit=1200),
            "full": dict(population_per_layer=64, generations=40, top_k=5, train_sample_limit=None, eval_sample_limit=None),
        }[mode]
        payload = {"mode": mode, **defaults, **{k: v for k, v in overrides.items() if v is not None}}
        return cls(**payload)

    def to_dict(self) -> Dict:
        return {
            "mode": self.mode,
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k": self.top_k,
            "seed": self.seed,
            "train_sample_limit": self.train_sample_limit,
            "eval_sample_limit": self.eval_sample_limit,
            "checkpoint_every": self.checkpoint_every,
        }


class LargeDatasetFullTrainingProbeTrainer:
    """Large Dataset Full Training Probe（大数据集全量训练探针）."""

    def __init__(self, train_samples: List[Dict], eval_samples: List[Dict], config: ProbeConfig):
        self.train_samples = list(train_samples[: config.train_sample_limit] if config.train_sample_limit else train_samples)
        self.eval_samples = list(eval_samples[: config.eval_sample_limit] if config.eval_sample_limit else eval_samples)
        self.config = config
        self.population = LayerPreservedPopulation.initialize(population_per_layer=config.population_per_layer, seed=config.seed)
        self.synthesis = AtomicSynthesis()
        self.curve: List[Dict] = []
        self.checkpoints: List[Dict] = []
        self.candidate_rows: List[Dict] = []

    def train(self) -> Dict:
        started = time.time()
        before = evaluate_dataset_stratified(self.population, self.train_samples + self.eval_samples, top_k=self.config.top_k)
        best_target = before["overall"]["target_ir_exact_match"]
        for generation in range(self.config.generations):
            records = []
            exact = 0
            false_accept = 0
            false_reject = 0
            for sample in self.train_samples:
                features = extract_surface_features(sample["input_text"])
                genomes = self.population.sample_candidate_paths(features, top_k=self.config.top_k)
                if not genomes:
                    continue
                best = None
                for candidate_index, genome in enumerate(genomes):
                    phenotype = self.synthesis.synthesize(genome, features)
                    fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
                    self._shape_training_reward(fitness, sample, phenotype)
                    record = CandidateRecord(genome, phenotype, fitness)
                    records.append(record)
                    if best is None or fitness.total_fitness > best.fitness_report.total_fitness:
                        best = record
                if best:
                    exact += int(best.fitness_report.target_ir_exact_match)
                    false_accept += int((not sample["supported"]) and not best.phenotype.unsupported_pred)
                    false_reject += int(sample["supported"] and best.phenotype.unsupported_pred)
                    if generation in {0, self.config.generations - 1} and len(self.candidate_rows) < 2000:
                        self.candidate_rows.append(_candidate_row(generation, sample, best))
            self.population.evolve(records)
            train_supported = max(sum(1 for sample in self.train_samples if sample["supported"]), 1)
            curve_row = {
                "generation": generation,
                "train_target_ir_exact_match": round(exact / train_supported, 4),
                "train_false_accept_unsupported_count": false_accept,
                "train_false_reject_supported_count": false_reject,
                "record_count": len(records),
            }
            self.curve.append(curve_row)
            best_target = max(best_target, curve_row["train_target_ir_exact_match"])
            if generation % self.config.checkpoint_every == 0 or generation == self.config.generations - 1:
                self.checkpoints.append(
                    {
                        "generation": generation,
                        "population_summary": self.population.summary(),
                        "train_metrics_snapshot": curve_row,
                        "best_target_ir_exact_match_so_far": best_target,
                    }
                )
        after_train = evaluate_dataset_stratified(self.population, self.train_samples, top_k=self.config.top_k)
        after_eval = evaluate_dataset_stratified(self.population, self.eval_samples, top_k=self.config.top_k)
        combined_after = evaluate_dataset_stratified(self.population, self.train_samples + self.eval_samples, top_k=self.config.top_k)
        runtime = round(time.time() - started, 4)
        return {
            "config": self.config.to_dict(),
            "train_sample_count": len(self.train_samples),
            "eval_sample_count": len(self.eval_samples),
            "runtime_seconds": runtime,
            "before_training_metrics": _strip_rows(before),
            "after_train_metrics": _strip_rows(after_train),
            "after_eval_metrics": _strip_rows(after_eval),
            "after_combined_metrics": _strip_rows(combined_after),
            "curve": self.curve,
            "checkpoints": self.checkpoints,
            "candidate_rows": self.candidate_rows,
        }

    def _shape_training_reward(self, fitness, sample, phenotype) -> None:
        if sample["supported"] and fitness.target_ir_exact_match and fitness.expected_output_match:
            fitness.total_fitness += 2.0
        if sample["supported"] and phenotype.unsupported_pred:
            fitness.total_fitness -= 2.0
        if (not sample["supported"]) and not phenotype.unsupported_pred:
            fitness.total_fitness -= 4.0
        if (not sample["supported"]) and phenotype.unsupported_pred:
            fitness.total_fitness += 2.0
        if sample.get("input_mode") == "unsupported_arithmetic" and phenotype.unsupported_pred:
            fitness.total_fitness += 1.0


def write_probe_outputs(metrics: Dict, records_dir: Path) -> Dict:
    records_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = records_dir / "large_training_probe_metrics.json"
    report_path = records_dir / "large_training_probe_report.md"
    candidates_path = records_dir / "large_training_probe_candidates.jsonl"
    curve_path = records_dir / "large_training_probe_curve.jsonl"
    checkpoints_path = records_dir / "large_training_probe_checkpoints.json"
    serializable = {k: v for k, v in metrics.items() if k != "candidate_rows"}
    metrics_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    candidates_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["candidate_rows"]),
        encoding="utf-8",
    )
    curve_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["curve"]),
        encoding="utf-8",
    )
    checkpoints_path.write_text(json.dumps(metrics["checkpoints"], ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(_report_markdown(metrics), encoding="utf-8")
    return {
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "candidates_path": str(candidates_path),
        "curve_path": str(curve_path),
        "checkpoints_path": str(checkpoints_path),
    }


def _strip_rows(metrics: Dict) -> Dict:
    return {key: value for key, value in metrics.items() if key != "rows"}


def _candidate_row(generation: int, sample: Dict, record: CandidateRecord) -> Dict:
    return {
        "generation": generation,
        "sample_id": sample["sample_id"],
        "split": sample["split"],
        "input_mode": sample["input_mode"],
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": record.phenotype.target_ir_canonical,
        "unsupported_pred": record.phenotype.unsupported_pred,
        "fitness": record.fitness_report.total_fitness,
        "rejected_by_layer": record.genome.branch_path.rejected_by_layer,
        "reject_type": record.genome.branch_path.reject_type,
    }


def _report_markdown(metrics: Dict) -> str:
    config = metrics["config"]
    before = metrics["before_training_metrics"]["overall"]
    after = metrics["after_combined_metrics"]["overall"]
    eval_metrics = metrics["after_eval_metrics"]
    diagnostics = eval_metrics["diagnostics"]
    lines = [
        "# v0.6.9 Large Dataset Full Training Probe（大数据集全量训练探针） Report",
        "",
        "This is a probe（探针）, not a release claim or convergence claim.",
        "",
        "## Parameter Config（参数配置）",
        "",
        f"- mode: {config['mode']}",
        f"- population_per_layer（每层种群数量）: {config['population_per_layer']}",
        f"- generations（训练代数）: {config['generations']}",
        f"- top_k_candidates（候选保留数量）: {config['top_k']}",
        f"- train sample count: {metrics['train_sample_count']}",
        f"- eval sample count: {metrics['eval_sample_count']}",
        f"- runtime seconds: {metrics['runtime_seconds']}",
        f"- runtime note（运行说明）: {_runtime_note(config)}",
        "",
        "## Before vs After（训练前后）",
        "",
        f"- before target_ir_exact_match（目标中间表示精确匹配）: {before['target_ir_exact_match']}",
        f"- after target_ir_exact_match（目标中间表示精确匹配）: {after['target_ir_exact_match']}",
        f"- after unsupported_rejection_rate（不支持拒绝率）: {after['unsupported_rejection_rate']}",
        f"- after false_accept_unsupported_rate（不支持误接收率）: {after['false_accept_unsupported_rate']}",
        "",
        "## Full-Split Evaluation（全切分评测）",
        "",
    ]
    for split, payload in eval_metrics["by_split"].items():
        lines.append(f"- {split}: target_ir_exact_match={payload['target_ir_exact_match']}, unsupported_rejection_rate={payload['unsupported_rejection_rate']}, false_accept_unsupported_rate={payload['false_accept_unsupported_rate']}")
    lines.extend(["", "## Stratified Evaluation（分层评测） by Input-Mode Metrics（输入模式指标）", ""])
    for mode, payload in eval_metrics["by_input_mode"].items():
        lines.append(f"- {mode}: target_ir_exact_match={payload['target_ir_exact_match']}, false_reject_supported_rate={payload['false_reject_supported_rate']}, false_accept_unsupported_rate={payload['false_accept_unsupported_rate']}")
    lines.extend(["", "## Expression-Family Metrics（表达式族指标）", ""])
    for family, payload in eval_metrics["by_expression_family"].items():
        lines.append(f"- {family}: target_ir_exact_match={payload['target_ir_exact_match']}, sample_count={payload['sample_count']}")
    lines.extend(
        [
            "",
            "## Known Diagnostic Targets（已知诊断目标）",
            "",
            f"- zh_number_expression false reject（中文数字表达误拒）: {diagnostics['zh_number_expression_false_reject_count']} / {diagnostics['zh_number_expression_false_reject_rate']}",
            f"- unsupported_arithmetic false accept（不支持算术误接收）: {diagnostics['unsupported_arithmetic_false_accept_count']} / {diagnostics['unsupported_arithmetic_false_accept_rate']}",
            f"- task_scope no-confident reject（任务范围层无可信拒绝）: {diagnostics['task_scope_no_confident_reject_count']}",
            f"- arithmetic_family typed reject（算术族类型化拒绝）: {diagnostics['arithmetic_family_typed_reject_count']}",
            f"- structure_policy typed reject（结构策略类型化拒绝）: {diagnostics['structure_policy_typed_reject_count']}",
            "",
            "## Training Curve（训练曲线）",
            "",
            "- " + ", ".join(f"g{row['generation']}={row['train_target_ir_exact_match']}" for row in metrics["curve"]),
            "",
            "## Non-Claims（非主张）",
            "",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
            "- This is a Large Dataset Full Training Probe（大数据集全量训练探针）, not a release claim.",
        ]
    )
    return "\n".join(lines) + "\n"


def _runtime_note(config: Dict) -> str:
    expected = {
        "quick": (16, 5, 3, 800, 400),
        "medium": (32, 20, 5, 2400, 1200),
        "full": (64, 40, 5, None, None),
    }
    baseline = expected.get(config["mode"])
    current = (
        config["population_per_layer"],
        config["generations"],
        config["top_k"],
        config["train_sample_limit"],
        config["eval_sample_limit"],
    )
    if baseline and current != baseline:
        return "bounded runtime override; default mode parameters were not fully completed"
    return "default mode parameters completed"
