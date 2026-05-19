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
from jianmu.self_learning.darwinforge.symbol_grounding_eval import evaluate_symbol_grounding


@dataclass
class SymbolGroundingConfig:
    mode: str = "medium"
    population_per_layer: int = 32
    generations: int = 20
    top_k: int = 5
    seed: int = 42
    train_limit: Optional[int] = 2200

    @classmethod
    def for_mode(cls, mode: str, **overrides) -> "SymbolGroundingConfig":
        defaults = {
            "quick": dict(population_per_layer=16, generations=5, top_k=3, train_limit=600),
            "medium": dict(population_per_layer=32, generations=20, top_k=5, train_limit=2200),
            "full": dict(population_per_layer=64, generations=40, top_k=5, train_limit=None),
        }[mode]
        payload = {"mode": mode, **defaults, **{key: value for key, value in overrides.items() if value is not None}}
        return cls(**payload)

    def to_dict(self) -> Dict:
        return {
            "mode": self.mode,
            "population_per_layer": self.population_per_layer,
            "generations": self.generations,
            "top_k": self.top_k,
            "seed": self.seed,
            "train_limit": self.train_limit,
        }


class SymbolGroundingCurriculumTrainer:
    """Symbol Grounding Curriculum（符号接地课程） trainer scaffold."""

    def __init__(self, train_samples: List[Dict], eval_samples: List[Dict], ood_samples: List[Dict], config: SymbolGroundingConfig):
        self.train_samples = train_samples[: config.train_limit] if config.train_limit else train_samples
        self.eval_samples = eval_samples
        self.ood_samples = ood_samples
        self.config = config
        self.population = LayerPreservedPopulation.initialize(population_per_layer=config.population_per_layer, seed=config.seed)
        self.synthesis = AtomicSynthesis()
        self.curve: List[Dict] = []
        self.candidate_rows: List[Dict] = []

    def train(self) -> Dict:
        started = time.time()
        before = evaluate_symbol_grounding(self.population, self.eval_samples + self.ood_samples, top_k=self.config.top_k)
        stage_order = ["numeral_grounding", "operator_grounding", "structure_grounding", "mixed_replay"]
        generations_per_stage = max(1, self.config.generations // len(stage_order))
        generation = 0
        for stage in stage_order:
            stage_samples = self.train_samples if stage == "mixed_replay" else [sample for sample in self.train_samples if sample["curriculum_stage"] == stage]
            for _ in range(generations_per_stage):
                if generation >= self.config.generations:
                    break
                row = self._train_generation(stage, stage_samples, generation)
                self.curve.append(row)
                generation += 1
        after_train = evaluate_symbol_grounding(self.population, self.train_samples, top_k=self.config.top_k)
        after_eval = evaluate_symbol_grounding(self.population, self.eval_samples, top_k=self.config.top_k)
        after_ood = evaluate_symbol_grounding(self.population, self.ood_samples, top_k=self.config.top_k)
        after_all = evaluate_symbol_grounding(self.population, self.train_samples + self.eval_samples + self.ood_samples, top_k=self.config.top_k)
        return {
            "config": self.config.to_dict(),
            "train_sample_count": len(self.train_samples),
            "eval_sample_count": len(self.eval_samples),
            "ood_sample_count": len(self.ood_samples),
            "runtime_seconds": round(time.time() - started, 4),
            "before_metrics": _strip_rows(before),
            "after_train_metrics": _strip_rows(after_train),
            "after_eval_metrics": _strip_rows(after_eval),
            "after_ood_metrics": _strip_rows(after_ood),
            "after_all_metrics": _strip_rows(after_all),
            "curve": self.curve,
            "candidate_rows": self.candidate_rows,
        }

    def _train_generation(self, stage: str, samples: List[Dict], generation: int) -> Dict:
        records = []
        exact = 0
        false_reject = 0
        for sample in samples:
            features = extract_surface_features(sample["input_text"])
            genomes = self.population.sample_candidate_paths(features, top_k=self.config.top_k)
            best = None
            for genome in genomes:
                phenotype = self.synthesis.synthesize(genome, features)
                fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
                self._shape_reward(fitness, sample, phenotype)
                record = CandidateRecord(genome, phenotype, fitness)
                records.append(record)
                if best is None or fitness.total_fitness > best.fitness_report.total_fitness:
                    best = record
            if best:
                exact += int(best.fitness_report.target_ir_exact_match)
                false_reject += int(sample["supported"] and best.phenotype.unsupported_pred)
                if len(self.candidate_rows) < 2000 and generation in {0, self.config.generations - 1}:
                    self.candidate_rows.append(_candidate_row(generation, stage, sample, best))
        self.population.evolve(records)
        supported_count = max(sum(1 for sample in samples if sample["supported"]), 1)
        return {
            "generation": generation,
            "stage": stage,
            "sample_count": len(samples),
            "target_ir_exact_match": round(exact / supported_count, 4),
            "false_reject_supported_count": false_reject,
            "record_count": len(records),
        }

    def _shape_reward(self, fitness, sample, phenotype) -> None:
        supported = sample["supported"]
        if supported and fitness.target_ir_exact_match:
            fitness.total_fitness += 4.0
        if supported and fitness.expected_output_match:
            fitness.total_fitness += 2.0
        if supported and not phenotype.unsupported_pred:
            fitness.total_fitness += 1.0
        if supported and phenotype.unsupported_pred:
            fitness.total_fitness -= 4.0
        if sample["input_mode"] == "zh_number_expression" and phenotype.unsupported_pred:
            fitness.total_fitness -= 6.0
        if sample["input_mode"] == "zh_number_expression" and fitness.target_ir_exact_match:
            fitness.total_fitness += 5.0
        if (not supported) and phenotype.unsupported_pred:
            fitness.total_fitness += 2.0
        if (not supported) and not phenotype.unsupported_pred:
            fitness.total_fitness -= 5.0
        if supported and phenotype.target_ir_canonical:
            fitness.total_fitness += _slot_bonus(phenotype.target_ir_canonical, sample)


def write_symbol_grounding_outputs(metrics: Dict, records_dir: Path) -> Dict:
    records_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = records_dir / "symbol_grounding_metrics.json"
    report_path = records_dir / "symbol_grounding_report.md"
    candidates_path = records_dir / "symbol_grounding_candidates.jsonl"
    curve_path = records_dir / "symbol_grounding_curve.jsonl"
    serializable = {key: value for key, value in metrics.items() if key != "candidate_rows"}
    metrics_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    candidates_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["candidate_rows"]), encoding="utf-8")
    curve_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics["curve"]), encoding="utf-8")
    report_path.write_text(_report_markdown(metrics), encoding="utf-8")
    return {
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "candidates_path": str(candidates_path),
        "curve_path": str(curve_path),
    }


def _slot_bonus(canonical: str, sample: Dict) -> float:
    bonus = 0.0
    for slot in sample.get("symbol_slots", []):
        bonus += 1.0 if f"lit({slot['target_literal']})" in canonical else 0.0
    for slot in sample.get("operator_slots", []):
        bonus += 1.0 if slot["target_operator"] in canonical else 0.0
    return bonus


def _candidate_row(generation: int, stage: str, sample: Dict, record: CandidateRecord) -> Dict:
    return {
        "generation": generation,
        "stage": stage,
        "sample_id": sample["sample_id"],
        "input_text": sample["input_text"],
        "input_mode": sample["input_mode"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": record.phenotype.target_ir_canonical,
        "unsupported_pred": record.phenotype.unsupported_pred,
        "fitness": record.fitness_report.total_fitness,
    }


def _strip_rows(metrics: Dict) -> Dict:
    return {key: value for key, value in metrics.items() if key != "rows"}


def _report_markdown(metrics: Dict) -> str:
    before_symbol = metrics["before_metrics"]["symbol_metrics"]
    after_symbol = metrics["after_eval_metrics"]["symbol_metrics"]
    after_ood = metrics["after_ood_metrics"]["overall"]
    lines = [
        "# v0.7.0 Symbol Grounding Curriculum（符号接地课程） Report",
        "",
        "This is a Symbol Grounding（符号接地） scaffold, not a convergence claim.",
        "",
        "## Config（配置）",
        "",
        f"- mode: {metrics['config']['mode']}",
        f"- population_per_layer（每层种群数量）: {metrics['config']['population_per_layer']}",
        f"- generations（训练代数）: {metrics['config']['generations']}",
        f"- top_k: {metrics['config']['top_k']}",
        f"- train/eval/ood: {metrics['train_sample_count']} / {metrics['eval_sample_count']} / {metrics['ood_sample_count']}",
        f"- runtime seconds: {metrics['runtime_seconds']}",
        "",
        "## Before vs After（训练前后）",
        "",
        f"- before zh_number_expression_false_reject_rate（中文数字表达误拒率）: {before_symbol['zh_number_expression_false_reject_rate']}",
        f"- after zh_number_expression_false_reject_rate（中文数字表达误拒率）: {after_symbol['zh_number_expression_false_reject_rate']}",
        f"- before zh_number_targetir_exact_match（中文数字表达 TargetIR 精确匹配）: {before_symbol['zh_number_targetir_exact_match']}",
        f"- after zh_number_targetir_exact_match（中文数字表达 TargetIR 精确匹配）: {after_symbol['zh_number_targetir_exact_match']}",
        f"- before symbol_slot_accuracy（符号槽位准确率）: {before_symbol['symbol_slot_accuracy']}",
        f"- after symbol_slot_accuracy（符号槽位准确率）: {after_symbol['symbol_slot_accuracy']}",
        f"- numeral_slot_accuracy（数字槽位准确率）: {after_symbol['numeral_slot_accuracy']}",
        f"- operator_slot_accuracy（运算符槽位准确率）: {after_symbol['operator_slot_accuracy']}",
        f"- paired_arabic_zh_agreement（阿拉伯数字/中文数字成对一致率）: {after_symbol['paired_arabic_zh_agreement']}",
        f"- paired_group_targetir_consistency（成对组 TargetIR 一致率）: {after_symbol['paired_group_targetir_consistency']}",
        f"- eval target_ir_exact_match（目标中间表示精确匹配）: {metrics['after_eval_metrics']['overall']['target_ir_exact_match']}",
        f"- ood_rejection_rate（分布外拒绝率）: {after_ood['unsupported_rejection_rate']}",
        f"- ood_false_accept_rate（分布外误接收率）: {after_ood['false_accept_unsupported_rate']}",
        "",
        "## Training Curve（训练曲线）",
        "",
        "- " + ", ".join(f"g{row['generation']}:{row['stage']}={row['target_ir_exact_match']}" for row in metrics["curve"]),
        "",
        "## Examples（样例）",
        "",
        "- 三加四",
        "- 十一减五",
        "- 负三乘四",
        "- 十二除以三",
        "- 三加四乘五",
        "",
        "## Non-Claims（非主张）",
        "",
        "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
        "- This does not prove general program synthesis.",
        "- This does not train C source text.",
        "- This does not patch old source code.",
        "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        "- This is a symbol grounding curriculum scaffold.",
    ]
    return "\n".join(lines) + "\n"

