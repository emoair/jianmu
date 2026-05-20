from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.surface_features import extract_canonical_surface_features, extract_surface_features
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def build_training_features(input_text: str, canonicalization_enabled: bool) -> Dict:
    if canonicalization_enabled:
        return extract_canonical_surface_features(input_text, canonicalization_enabled=True)
    features = extract_surface_features(input_text)
    features.update(
        {
            "raw_text": input_text,
            "canonical_text": input_text,
            "canonicalization_enabled": False,
            "canonical_changed": False,
            "canonical_token_count": 0,
            "source_map_coverage": 0.0,
        }
    )
    return features


def evaluate_canonicalized_training(
    population,
    samples: List[Dict],
    top_k: int = 5,
    canonicalization_enabled: bool = True,
    sample_limit: Optional[int] = None,
) -> Dict:
    """Canonicalized Training Probe（规范化输入训练探针） evaluation."""
    selected = list(samples[:sample_limit] if sample_limit is not None else samples)
    synthesis = AtomicSynthesis()
    rows = []
    for sample in selected:
        canonical = canonicalize_symbols(sample["input_text"])
        features = build_training_features(sample["input_text"], canonicalization_enabled)
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
        "canonical_metrics": _canonical_metrics(rows, canonicalization_enabled),
        "zh_number_metrics": _zh_number_metrics(rows),
        "known_diagnostics": _known_diagnostics(rows),
        "by_input_mode": _group(rows, "input_mode"),
        "by_curriculum_stage": _group(rows, "curriculum_stage"),
        "by_structure_policy": _group(rows, "structure_policy"),
        "rows": rows,
    }


def _row(sample, canonical, enabled, genome, phenotype, fitness) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "raw_text": sample["input_text"],
        "canonical_text": canonical.canonical_text,
        "source_map": canonical.source_map,
        "canonicalization_enabled": enabled,
        "canonical_changed": canonical.changed,
        "source_map_coverage": _source_map_coverage(canonical),
        "input_mode": sample.get("input_mode"),
        "curriculum_stage": sample.get("curriculum_stage"),
        "structure_policy": sample.get("structure_policy"),
        "expression_family": sample.get("expression_family"),
        "unsupported_reason": sample.get("unsupported_reason"),
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": phenotype.target_ir_canonical,
        "unsupported_pred": phenotype.unsupported_pred,
        "target_ir_exact_match": fitness.target_ir_exact_match,
        "expected_output_match": fitness.expected_output_match,
        "false_reject_supported": bool(sample["supported"] and phenotype.unsupported_pred),
        "false_accept_unsupported": bool((not sample["supported"]) and not phenotype.unsupported_pred),
        "task_scope_continued": any(decision.layer_name == "task_scope" and decision.selected == "programming" for decision in genome.branch_path.decisions),
        "candidate_generation_success": True,
        "rejected_by_layer": genome.branch_path.rejected_by_layer,
        "reject_type": genome.branch_path.reject_type,
    }


def _missing_row(sample, canonical, enabled) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "raw_text": sample["input_text"],
        "canonical_text": canonical.canonical_text,
        "source_map": canonical.source_map,
        "canonicalization_enabled": enabled,
        "canonical_changed": canonical.changed,
        "source_map_coverage": _source_map_coverage(canonical),
        "input_mode": sample.get("input_mode"),
        "curriculum_stage": sample.get("curriculum_stage"),
        "structure_policy": sample.get("structure_policy"),
        "expression_family": sample.get("expression_family"),
        "unsupported_reason": sample.get("unsupported_reason"),
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": None,
        "unsupported_pred": False,
        "target_ir_exact_match": False,
        "expected_output_match": False,
        "false_reject_supported": False,
        "false_accept_unsupported": not sample["supported"],
        "task_scope_continued": False,
        "candidate_generation_success": False,
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
        "candidate_generation_success_rate": _rate(rows, "candidate_generation_success"),
    }


def _canonical_metrics(rows: List[Dict], enabled: bool) -> Dict:
    return {
        "canonicalization_enabled": enabled,
        "canonicalization_success_rate": round(sum(1 for row in rows if row["canonical_text"]) / max(len(rows), 1), 4),
        "canonical_changed_rate": _rate(rows, "canonical_changed"),
        "source_map_coverage": round(sum(row["source_map_coverage"] for row in rows) / max(len(rows), 1), 4),
    }


def _zh_number_metrics(rows: List[Dict]) -> Dict:
    zh_rows = [row for row in rows if row["input_mode"] == "zh_number_expression" and row["supported"]]
    return {
        "zh_number_expression_false_reject_rate": _rate(zh_rows, "false_reject_supported"),
        "zh_number_targetir_exact_match": _rate(zh_rows, "target_ir_exact_match"),
        "zh_number_task_scope_continue_rate": _rate(zh_rows, "task_scope_continued"),
    }


def _known_diagnostics(rows: List[Dict]) -> Dict:
    supported = [row for row in rows if row["supported"]]
    negative = [row for row in supported if "负" in row["raw_text"] or "-" in row["raw_text"]]
    parentheses = [row for row in supported if row.get("structure_policy") == "parenthesized_tree"]
    mixed = [row for row in supported if row.get("structure_policy") == "precedence_tree"]
    division = [row for row in supported if row.get("expression_family") == "exact_division"]
    unsupported_arithmetic = [row for row in rows if row["input_mode"] == "unsupported_arithmetic" or row.get("unsupported_reason") in {"non_exact_division", "division_by_zero"}]
    ood = [row for row in rows if not row["supported"]]
    return {
        "negative_number_targetir_exact_match": _rate(negative, "target_ir_exact_match"),
        "parentheses_targetir_exact_match": _rate(parentheses, "target_ir_exact_match"),
        "mixed_precedence_targetir_exact_match": _rate(mixed, "target_ir_exact_match"),
        "exact_division_targetir_exact_match": _rate(division, "target_ir_exact_match"),
        "unsupported_arithmetic_false_accept_rate": _rate(unsupported_arithmetic, "false_accept_unsupported"),
        "ood_false_accept_rate": _rate(ood, "false_accept_unsupported"),
    }


def _group(rows: List[Dict], key: str) -> Dict[str, Dict]:
    buckets = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key))].append(row)
    return {name: _aggregate(bucket) for name, bucket in sorted(buckets.items())}


def _source_map_coverage(canonical) -> float:
    non_text = [token for token in canonical.tokens if token.token_type != "TEXT"]
    mapped = [token for token in non_text if token.raw and token.canonical]
    return round(len(mapped) / max(len(non_text), 1), 4)


def _rate(rows: List[Dict], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)

