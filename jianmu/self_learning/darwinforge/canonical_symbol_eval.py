from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def evaluate_canonical_symbol_layer(
    population,
    samples: List[Dict],
    top_k: int = 5,
    sample_limit: Optional[int] = None,
    canonicalization_enabled: bool = True,
) -> Dict:
    """Canonical Symbol Layer（规范符号层） evaluation with labels used only after prediction."""
    selected = list(samples[:sample_limit] if sample_limit is not None else samples)
    synthesis = AtomicSynthesis()
    rows = []
    for sample in selected:
        canonical = canonicalize_symbols(sample["input_text"])
        routed_text = canonical.canonical_text if canonicalization_enabled and canonical.canonical_text else sample["input_text"]
        features = extract_surface_features(routed_text)
        if canonicalization_enabled:
            features.update(
                {
                    "raw_text": sample["input_text"],
                    "canonical_text": canonical.canonical_text,
                    "canonical_changed": canonical.changed,
                    "canonical_token_count": len(canonical.tokens),
                    "source_map_coverage": _source_map_coverage(canonical),
                    "contains_canonicalized_zh_number": any(
                        token.token_type == "NUM" and token.raw != token.canonical for token in canonical.tokens
                    ),
                    "contains_canonicalized_zh_operator": any(
                        token.token_type.startswith("OP_") and token.raw != token.canonical for token in canonical.tokens
                    ),
                }
            )
        genomes = population.sample_candidate_paths(features, top_k=top_k)
        if not genomes:
            rows.append(_missing_row(sample, canonical, canonicalization_enabled))
            continue
        best = None
        for genome in genomes:
            phenotype = synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
            record = (fitness.total_fitness, genome, phenotype, fitness)
            if best is None or record[0] > best[0]:
                best = record
        _, genome, phenotype, fitness = best
        rows.append(_row(sample, canonical, canonicalization_enabled, genome, phenotype, fitness))
    return {
        "overall": _aggregate(rows),
        "canonical_metrics": _canonical_metrics(rows),
        "zh_number_metrics": _zh_number_metrics(rows),
        "ood_metrics": _ood_metrics(rows),
        "rows": rows,
    }


def compare_canonical_symbol_layer(population, samples: List[Dict], top_k: int = 5, sample_limit: Optional[int] = None) -> Dict:
    without = evaluate_canonical_symbol_layer(population, samples, top_k, sample_limit, canonicalization_enabled=False)
    with_canonical = evaluate_canonical_symbol_layer(population, samples, top_k, sample_limit, canonicalization_enabled=True)
    return {
        "without_canonicalization": _without_rows(without),
        "with_canonicalization": _without_rows(with_canonical),
        "delta": {
            "target_ir_exact_match": round(
                with_canonical["overall"]["target_ir_exact_match"] - without["overall"]["target_ir_exact_match"], 4
            ),
            "zh_number_expression_false_reject_rate": round(
                with_canonical["zh_number_metrics"]["zh_number_expression_false_reject_rate"]
                - without["zh_number_metrics"]["zh_number_expression_false_reject_rate"],
                4,
            ),
            "zh_number_targetir_exact_match": round(
                with_canonical["zh_number_metrics"]["zh_number_targetir_exact_match"]
                - without["zh_number_metrics"]["zh_number_targetir_exact_match"],
                4,
            ),
            "raw_vs_canonical_targetir_gap": round(
                with_canonical["overall"]["target_ir_exact_match"] - without["overall"]["target_ir_exact_match"], 4
            ),
        },
        "rows_without": without["rows"],
        "rows_with": with_canonical["rows"],
    }


def write_canonical_symbol_outputs(metrics: Dict, records_dir: str | Path) -> Dict[str, str]:
    records_path = Path(records_dir)
    records_path.mkdir(parents=True, exist_ok=True)
    metrics_path = records_path / "canonical_symbol_metrics.json"
    report_path = records_path / "canonical_symbol_report.md"
    candidates_path = records_path / "canonical_symbol_candidates.jsonl"
    examples_path = records_path / "canonical_symbol_examples.json"
    serializable = {key: value for key, value in metrics.items() if key not in {"rows_without", "rows_with"}}
    metrics_path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = metrics.get("rows_with", [])
    candidates_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")
    examples = _example_rows(rows)
    examples_path.write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(_report(metrics, examples), encoding="utf-8")
    return {
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "candidates_path": str(candidates_path),
        "examples_path": str(examples_path),
    }


def _row(sample, canonical, enabled, genome, phenotype, fitness) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "input_text": sample["input_text"],
        "canonicalization_enabled": enabled,
        "canonical_text": canonical.canonical_text,
        "canonical_changed": canonical.changed,
        "source_map": canonical.source_map,
        "source_map_coverage": _source_map_coverage(canonical),
        "warnings": canonical.warnings,
        "input_mode": sample.get("input_mode"),
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": phenotype.target_ir_canonical,
        "unsupported_pred": phenotype.unsupported_pred,
        "target_ir_exact_match": fitness.target_ir_exact_match,
        "expected_output_match": fitness.expected_output_match,
        "false_reject_supported": bool(sample["supported"] and phenotype.unsupported_pred),
        "false_accept_unsupported": bool((not sample["supported"]) and not phenotype.unsupported_pred),
        "task_scope_continued": any(decision.layer_name == "task_scope" and decision.selected == "programming" for decision in genome.branch_path.decisions),
        "rejected_by_layer": genome.branch_path.rejected_by_layer,
        "reject_type": genome.branch_path.reject_type,
    }


def _missing_row(sample, canonical, enabled) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "input_text": sample["input_text"],
        "canonicalization_enabled": enabled,
        "canonical_text": canonical.canonical_text,
        "canonical_changed": canonical.changed,
        "source_map": canonical.source_map,
        "source_map_coverage": _source_map_coverage(canonical),
        "warnings": canonical.warnings,
        "input_mode": sample.get("input_mode"),
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": None,
        "unsupported_pred": False,
        "target_ir_exact_match": False,
        "expected_output_match": False,
        "false_reject_supported": False,
        "false_accept_unsupported": not sample["supported"],
        "task_scope_continued": False,
        "rejected_by_layer": "missing_candidate",
        "reject_type": "missing_layer",
    }


def _aggregate(rows: List[Dict]) -> Dict:
    supported = [row for row in rows if row["supported"]]
    unsupported = [row for row in rows if not row["supported"]]
    return {
        "sample_count": len(rows),
        "target_ir_exact_match": _rate(supported, "target_ir_exact_match"),
        "expected_output_match": _rate(supported, "expected_output_match"),
        "unsupported_rejection_rate": _rate(unsupported, "unsupported_pred"),
        "false_reject_supported_rate": _rate(supported, "false_reject_supported"),
        "false_accept_unsupported_rate": _rate(unsupported, "false_accept_unsupported"),
    }


def _canonical_metrics(rows: List[Dict]) -> Dict:
    return {
        "canonicalization_success_rate": round(sum(1 for row in rows if row["canonical_text"]) / max(len(rows), 1), 4),
        "canonical_changed_rate": _rate(rows, "canonical_changed"),
        "source_map_coverage": round(sum(row["source_map_coverage"] for row in rows) / max(len(rows), 1), 4),
        "canonical_warning_count": sum(len(row.get("warnings", [])) for row in rows),
        "canonical_input_rejection_rate": _rate(rows, "unsupported_pred"),
    }


def _zh_number_metrics(rows: List[Dict]) -> Dict:
    zh_rows = [row for row in rows if row["input_mode"] == "zh_number_expression" and row["supported"]]
    return {
        "zh_number_expression_false_reject_rate": _rate(zh_rows, "false_reject_supported"),
        "zh_number_targetir_exact_match": _rate(zh_rows, "target_ir_exact_match"),
        "zh_number_task_scope_continue_rate": _rate(zh_rows, "task_scope_continued"),
    }


def _ood_metrics(rows: List[Dict]) -> Dict:
    unsupported = [row for row in rows if not row["supported"]]
    return {
        "ood_rejection_rate": _rate(unsupported, "unsupported_pred"),
        "ood_false_accept_rate": _rate(unsupported, "false_accept_unsupported"),
    }


def _source_map_coverage(canonical) -> float:
    non_text = [token for token in canonical.tokens if token.token_type != "TEXT"]
    mapped = [token for token in non_text if token.raw and token.canonical]
    return round(len(mapped) / max(len(non_text), 1), 4)


def _rate(rows: List[Dict], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)


def _without_rows(metrics: Dict) -> Dict:
    return {key: value for key, value in metrics.items() if key != "rows"}


def _example_rows(rows: List[Dict]) -> List[Dict]:
    wanted = ["三加四", "十一减五", "负三乘四", "十二除以三", "三加四乘五", "括号里三加四再乘五"]
    examples = []
    by_input = {row["input_text"]: row for row in rows}
    for text in wanted:
        if text in by_input:
            examples.append(by_input[text])
        else:
            canonical = canonicalize_symbols(text)
            examples.append(
                {
                    "input_text": text,
                    "canonical_text": canonical.canonical_text,
                    "source_map": canonical.source_map,
                    "target_ir_pred": None,
                    "target_ir_true": None,
                    "target_ir_exact_match": False,
                }
            )
    return examples


def _report(metrics: Dict, examples: List[Dict]) -> str:
    with_canonical = metrics["with_canonicalization"]
    without = metrics["without_canonicalization"]
    delta = metrics["delta"]
    lines = [
        "# Canonical Symbol Layer（规范符号层） Report",
        "",
        "## Summary（摘要）",
        f"- canonicalization_success_rate（规范化成功率）: {with_canonical['canonical_metrics']['canonicalization_success_rate']}",
        f"- source_map_coverage（源映射覆盖率）: {with_canonical['canonical_metrics']['source_map_coverage']}",
        f"- raw_vs_canonical_targetir_gap（原始输入与规范输入差距）: {delta['raw_vs_canonical_targetir_gap']}",
        f"- Source Map（源映射） coverage: {with_canonical['canonical_metrics']['source_map_coverage']}",
        "",
        "## On/Off Comparison（开关对比）",
        f"- without canonicalization zh_number_expression_false_reject_rate（关闭规范化中文数字误拒率）: {without['zh_number_metrics']['zh_number_expression_false_reject_rate']}",
        f"- with canonicalization zh_number_expression_false_reject_rate（开启规范化中文数字误拒率）: {with_canonical['zh_number_metrics']['zh_number_expression_false_reject_rate']}",
        f"- without canonicalization zh_number_targetir_exact_match（关闭规范化中文数字 TargetIR 精确匹配）: {without['zh_number_metrics']['zh_number_targetir_exact_match']}",
        f"- with canonicalization zh_number_targetir_exact_match（开启规范化中文数字 TargetIR 精确匹配）: {with_canonical['zh_number_metrics']['zh_number_targetir_exact_match']}",
        "",
        "## OOD Evaluation（分布外评测）",
        f"- ood_rejection_rate（分布外拒绝率）: {with_canonical['ood_metrics']['ood_rejection_rate']}",
        f"- ood_false_accept_rate（分布外误接收率）: {with_canonical['ood_metrics']['ood_false_accept_rate']}",
        "",
        "## Examples（示例）",
        "| Raw Text（原始文本） | Canonical Text（规范文本） | Exact（精确） |",
        "|---|---|---|",
    ]
    for row in examples:
        lines.append(f"| {row['input_text']} | {row['canonical_text']} | {row.get('target_ir_exact_match', False)} |")
    lines.extend(
        [
            "",
            "## Non-Claims（非主张）",
            "- This does not prove stable DarwinForge（达尔文进化炉） convergence.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This does not patch old source code.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
            "- This is a Canonical Symbol Layer（规范符号层） canonicalization experiment, not a convergence claim.",
        ]
    )
    return "\n".join(lines) + "\n"
