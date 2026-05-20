from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateRecord
from jianmu.self_learning.darwinforge.canonicalized_training_eval import (
    build_training_features,
    evaluate_canonicalized_training,
)
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


@dataclass
class CanonicalizedTrainingConfig:
    mode: str = "medium"
    canonicalization_enabled: bool = True
    population_per_layer: int = 32
    generations: int = 20
    top_k: int = 5
    seed: int = 42
    train_limit: Optional[int] = 2200
    eval_limit: Optional[int] = 600
    ood_limit: Optional[int] = 200

    @classmethod
    def for_mode(cls, mode: str, canonicalization_enabled: bool, **overrides) -> "CanonicalizedTrainingConfig":
        defaults = {
            "quick": dict(population_per_layer=16, generations=5, top_k=3, train_limit=600, eval_limit=300, ood_limit=100),
            "medium": dict(population_per_layer=32, generations=20, top_k=5, train_limit=2200, eval_limit=600, ood_limit=200),
            "full": dict(population_per_layer=64, generations=40, top_k=5, train_limit=None, eval_limit=None, ood_limit=None),
        }[mode]
        payload = {
            "mode": mode,
            "canonicalization_enabled": canonicalization_enabled,
            **defaults,
            **{key: value for key, value in overrides.items() if value is not None},
        }
        return cls(**payload)

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


class CanonicalizedTrainingProbeTrainer:
    """Canonicalized Training Probe（规范化输入训练探针） using BranchChain（分支链）."""

    def __init__(self, train_samples: List[Dict], eval_samples: List[Dict], ood_samples: List[Dict], config: CanonicalizedTrainingConfig):
        self.config = config
        self.train_samples = train_samples[: config.train_limit] if config.train_limit else train_samples
        self.eval_samples = eval_samples[: config.eval_limit] if config.eval_limit else eval_samples
        self.ood_samples = ood_samples[: config.ood_limit] if config.ood_limit else ood_samples
        self.population = LayerPreservedPopulation.initialize(population_per_layer=config.population_per_layer, seed=config.seed)
        self.synthesis = AtomicSynthesis()
        self.curve: List[Dict] = []
        self.candidate_rows: List[Dict] = []

    def train(self) -> Dict:
        started = time.time()
        before = evaluate_canonicalized_training(
            self.population,
            self.eval_samples + self.ood_samples,
            self.config.top_k,
            self.config.canonicalization_enabled,
        )
        for generation in range(self.config.generations):
            row = self._train_generation(generation)
            self.curve.append(row)
        after_train = evaluate_canonicalized_training(self.population, self.train_samples, self.config.top_k, self.config.canonicalization_enabled)
        after_eval = evaluate_canonicalized_training(self.population, self.eval_samples, self.config.top_k, self.config.canonicalization_enabled)
        after_ood = evaluate_canonicalized_training(self.population, self.ood_samples, self.config.top_k, self.config.canonicalization_enabled)
        after_all = evaluate_canonicalized_training(
            self.population,
            self.train_samples + self.eval_samples + self.ood_samples,
            self.config.top_k,
            self.config.canonicalization_enabled,
        )
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

    def _train_generation(self, generation: int) -> Dict:
        records = []
        exact = 0
        false_reject = 0
        for sample in self.train_samples:
            canonical = canonicalize_symbols(sample["input_text"])
            features = build_training_features(sample["input_text"], self.config.canonicalization_enabled)
            genomes = self.population.sample_candidate_paths(features, top_k=self.config.top_k)
            best = None
            for genome in genomes:
                phenotype = self.synthesis.synthesize(genome, features)
                fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
                self._shape_reward(fitness, sample, phenotype, canonical)
                record = CandidateRecord(genome, phenotype, fitness)
                records.append(record)
                if best is None or fitness.total_fitness > best.fitness_report.total_fitness:
                    best = record
            if best:
                exact += int(best.fitness_report.target_ir_exact_match)
                false_reject += int(sample["supported"] and best.phenotype.unsupported_pred)
                if len(self.candidate_rows) < 3000 and generation in {0, self.config.generations - 1}:
                    self.candidate_rows.append(_candidate_row(generation, sample, canonical, best, self.config.canonicalization_enabled))
        self.population.evolve(records)
        supported_count = max(sum(1 for sample in self.train_samples if sample["supported"]), 1)
        return {
            "generation": generation,
            "canonicalization_enabled": self.config.canonicalization_enabled,
            "sample_count": len(self.train_samples),
            "target_ir_exact_match": round(exact / supported_count, 4),
            "false_reject_supported_count": false_reject,
            "record_count": len(records),
        }

    def _shape_reward(self, fitness, sample, phenotype, canonical) -> None:
        supported = sample["supported"]
        if supported and fitness.target_ir_exact_match:
            fitness.total_fitness += 4.0
        if supported and fitness.expected_output_match:
            fitness.total_fitness += 2.0
        if supported and not phenotype.unsupported_pred:
            fitness.total_fitness += 1.0
        if supported and phenotype.unsupported_pred:
            fitness.total_fitness -= 4.0
        if sample.get("input_mode") == "zh_number_expression" and phenotype.unsupported_pred:
            fitness.total_fitness -= 6.0
        if sample.get("input_mode") == "zh_number_expression" and fitness.target_ir_exact_match:
            fitness.total_fitness += 5.0
        if (not supported) and phenotype.unsupported_pred:
            fitness.total_fitness += 2.0
        if (not supported) and not phenotype.unsupported_pred:
            fitness.total_fitness -= 5.0
        if self.config.canonicalization_enabled and canonical.changed and supported and fitness.target_ir_exact_match:
            fitness.total_fitness += 2.0
        if self.config.canonicalization_enabled and canonical.changed and (not supported) and not phenotype.unsupported_pred:
            fitness.total_fitness -= 2.0


def compare_raw_and_canonical(train_samples: List[Dict], eval_samples: List[Dict], ood_samples: List[Dict], raw_config: CanonicalizedTrainingConfig, canonical_config: CanonicalizedTrainingConfig) -> Dict:
    raw = CanonicalizedTrainingProbeTrainer(train_samples, eval_samples, ood_samples, raw_config).train()
    canonical = CanonicalizedTrainingProbeTrainer(train_samples, eval_samples, ood_samples, canonical_config).train()
    return {
        "raw_training": _strip_candidate_rows(raw),
        "canonical_training": _strip_candidate_rows(canonical),
        "delta": _delta(raw, canonical),
        "candidate_rows": [
            *[_tag_row(row, "raw") for row in raw["candidate_rows"]],
            *[_tag_row(row, "canonical") for row in canonical["candidate_rows"]],
        ],
        "curve_raw": raw["curve"],
        "curve_canonical": canonical["curve"],
    }


def write_canonicalized_training_outputs(metrics: Dict, records_dir: Path) -> Dict[str, str]:
    records_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = records_dir / "canonicalized_training_metrics.json"
    report_path = records_dir / "canonicalized_training_report.md"
    curve_raw_path = records_dir / "canonicalized_training_curve_raw.jsonl"
    curve_canonical_path = records_dir / "canonicalized_training_curve_canonical.jsonl"
    candidates_path = records_dir / "canonicalized_training_candidates.jsonl"
    examples_path = records_dir / "canonicalized_training_examples.json"
    metrics_path.write_text(json.dumps({k: v for k, v in metrics.items() if k != "candidate_rows"}, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    curve_raw_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics.get("curve_raw", [])), encoding="utf-8")
    curve_canonical_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics.get("curve_canonical", [])), encoding="utf-8")
    candidates_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in metrics.get("candidate_rows", [])), encoding="utf-8")
    examples = _examples(metrics.get("candidate_rows", []))
    examples_path.write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(_report_markdown(metrics, examples), encoding="utf-8")
    return {
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "curve_raw_path": str(curve_raw_path),
        "curve_canonical_path": str(curve_canonical_path),
        "candidates_path": str(candidates_path),
        "examples_path": str(examples_path),
    }


def _candidate_row(generation: int, sample: Dict, canonical, record: CandidateRecord, enabled: bool) -> Dict:
    return {
        "generation": generation,
        "canonicalization_enabled": enabled,
        "sample_id": sample["sample_id"],
        "raw_text": sample["input_text"],
        "canonical_text": canonical.canonical_text,
        "source_map": canonical.source_map,
        "input_mode": sample.get("input_mode"),
        "structure_policy": sample.get("structure_policy"),
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": record.phenotype.target_ir_canonical,
        "unsupported_pred": record.phenotype.unsupported_pred,
        "target_ir_exact_match": record.fitness_report.target_ir_exact_match,
        "fitness": record.fitness_report.total_fitness,
    }


def _delta(raw: Dict, canonical: Dict) -> Dict:
    raw_eval = raw["after_eval_metrics"]
    can_eval = canonical["after_eval_metrics"]
    raw_ood = raw["after_ood_metrics"]
    can_ood = canonical["after_ood_metrics"]
    return {
        "target_ir_exact_match": round(can_eval["overall"]["target_ir_exact_match"] - raw_eval["overall"]["target_ir_exact_match"], 4),
        "zh_number_expression_false_reject_rate": round(can_eval["zh_number_metrics"]["zh_number_expression_false_reject_rate"] - raw_eval["zh_number_metrics"]["zh_number_expression_false_reject_rate"], 4),
        "zh_number_targetir_exact_match": round(can_eval["zh_number_metrics"]["zh_number_targetir_exact_match"] - raw_eval["zh_number_metrics"]["zh_number_targetir_exact_match"], 4),
        "ood_false_accept_rate": round(can_ood["overall"]["false_accept_unsupported_rate"] - raw_ood["overall"]["false_accept_unsupported_rate"], 4),
    }


def _strip_rows(metrics: Dict) -> Dict:
    return {key: value for key, value in metrics.items() if key != "rows"}


def _strip_candidate_rows(metrics: Dict) -> Dict:
    return {key: value for key, value in metrics.items() if key != "candidate_rows"}


def _tag_row(row: Dict, mode: str) -> Dict:
    tagged = dict(row)
    tagged["training_mode"] = mode
    return tagged


def _examples(rows: List[Dict]) -> List[Dict]:
    wanted = ["三加四", "十一减五", "负三乘四", "十二除以三", "三加四乘五", "括号里三加四再乘五"]
    examples = []
    for text in wanted:
        matching = [row for row in rows if row["raw_text"] == text]
        if matching:
            raw = next((row for row in matching if row["training_mode"] == "raw"), None)
            can = next((row for row in matching if row["training_mode"] == "canonical"), None)
            examples.append(
                {
                    "raw_text": text,
                    "canonical_text": (can or raw)["canonical_text"],
                    "raw_pred": raw.get("target_ir_pred") if raw else None,
                    "canonical_pred": can.get("target_ir_pred") if can else None,
                    "target_ir_true": (can or raw).get("target_ir_true"),
                    "raw_exact": raw.get("target_ir_exact_match") if raw else False,
                    "canonical_exact": can.get("target_ir_exact_match") if can else False,
                }
            )
    return examples


def _report_markdown(metrics: Dict, examples: List[Dict]) -> str:
    raw = metrics["raw_training"]
    canonical = metrics["canonical_training"]
    delta = metrics["delta"]
    raw_eval = raw["after_eval_metrics"]
    can_eval = canonical["after_eval_metrics"]
    raw_ood = raw["after_ood_metrics"]
    can_ood = canonical["after_ood_metrics"]
    can_diag = can_eval["known_diagnostics"]
    lines = [
        "# Canonicalized Training Probe（规范化输入训练探针） Report",
        "",
        "## Config（配置）",
        f"- mode: {canonical['config']['mode']}",
        f"- population_per_layer（每层种群数量）: {canonical['config']['population_per_layer']}",
        f"- generations（训练代数）: {canonical['config']['generations']}",
        f"- top_k（候选保留数量）: {canonical['config']['top_k']}",
        f"- train/eval/ood: {canonical['train_sample_count']} / {canonical['eval_sample_count']} / {canonical['ood_sample_count']}",
        "",
        "## Raw Input Training（原始输入训练） vs Canonical Input Training（规范输入训练）",
        f"- raw final target_ir_exact_match（原始输入 TargetIR 精确匹配）: {raw_eval['overall']['target_ir_exact_match']}",
        f"- canonical final target_ir_exact_match（规范输入 TargetIR 精确匹配）: {can_eval['overall']['target_ir_exact_match']}",
        f"- raw zh_number_expression_false_reject_rate（原始中文数字误拒率）: {raw_eval['zh_number_metrics']['zh_number_expression_false_reject_rate']}",
        f"- canonical zh_number_expression_false_reject_rate（规范中文数字误拒率）: {can_eval['zh_number_metrics']['zh_number_expression_false_reject_rate']}",
        f"- raw zh_number_targetir_exact_match（原始中文数字 TargetIR 精确匹配）: {raw_eval['zh_number_metrics']['zh_number_targetir_exact_match']}",
        f"- canonical zh_number_targetir_exact_match（规范中文数字 TargetIR 精确匹配）: {can_eval['zh_number_metrics']['zh_number_targetir_exact_match']}",
        f"- raw ood_false_accept_rate（原始分布外误接收率）: {raw_ood['overall']['false_accept_unsupported_rate']}",
        f"- canonical ood_false_accept_rate（规范分布外误接收率）: {can_ood['overall']['false_accept_unsupported_rate']}",
        f"- OOD Evaluation（分布外评测） raw/canonical false accept: {raw_ood['overall']['false_accept_unsupported_rate']} / {can_ood['overall']['false_accept_unsupported_rate']}",
        f"- raw_vs_canonical_delta（原始与规范差值）: {delta}",
        "",
        "## Stratified Evaluation（分层评测）",
        f"- negative_number_targetir_exact_match（负数 TargetIR 精确匹配）: {can_diag['negative_number_targetir_exact_match']}",
        f"- parentheses_targetir_exact_match（括号 TargetIR 精确匹配）: {can_diag['parentheses_targetir_exact_match']}",
        f"- mixed_precedence_targetir_exact_match（混合优先级 TargetIR 精确匹配）: {can_diag['mixed_precedence_targetir_exact_match']}",
        f"- exact_division_targetir_exact_match（精确除法 TargetIR 精确匹配）: {can_diag['exact_division_targetir_exact_match']}",
        f"- unsupported_arithmetic_false_accept_rate（不支持算术误接收率）: {can_diag['unsupported_arithmetic_false_accept_rate']}",
        "",
        "## Examples（示例）",
        "| raw_text（原始文本） | canonical_text（规范文本） | raw_pred | canonical_pred | target_ir_true | raw_exact | canonical_exact |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in examples:
        lines.append(
            f"| {row['raw_text']} | {row['canonical_text']} | {row.get('raw_pred')} | {row.get('canonical_pred')} | {row.get('target_ir_true')} | {row.get('raw_exact')} | {row.get('canonical_exact')} |"
        )
    lines.extend(
        [
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
            "- This is a Canonicalized Training Probe（规范化输入训练探针）, not a release claim.",
        ]
    )
    return "\n".join(lines) + "\n"
