from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.fitness import compute_fitness


def evaluate_dataset_stratified(population, dataset: List[Dict], top_k: int = 3, sample_limit: Optional[int] = None) -> Dict:
    """Full-Split Evaluation（全切分评测） and Stratified Evaluation（分层评测）."""
    rows = []
    synthesis = AtomicSynthesis()
    samples = list(dataset[:sample_limit] if sample_limit is not None else dataset)
    for sample in samples:
        features = extract_surface_features(sample["input_text"])
        genomes = population.sample_candidate_paths(features, top_k=top_k)
        if not genomes:
            rows.append(_missing_row(sample))
            continue
        best_record = None
        for genome in genomes:
            phenotype = synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
            record = (fitness.total_fitness, genome, phenotype, fitness)
            if best_record is None or record[0] > best_record[0]:
                best_record = record
        _, genome, phenotype, fitness = best_record
        rows.append(_row_from_prediction(sample, genome, phenotype, fitness, len(genomes)))
    return _metrics_from_rows(rows)


def _row_from_prediction(sample, genome, phenotype, fitness, candidate_count: int) -> Dict:
    early_exit = bool(genome.branch_path.early_exit)
    return {
        "sample_id": sample["sample_id"],
        "split": sample["split"],
        "input_mode": sample["input_mode"],
        "expression_family": sample.get("expression_family"),
        "structure_policy": sample.get("structure_policy"),
        "unsupported_reason": sample.get("unsupported_reason"),
        "supported": bool(sample["supported"]),
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": phenotype.target_ir_canonical,
        "unsupported_pred": bool(phenotype.unsupported_pred),
        "target_ir_exact_match": bool(fitness.target_ir_exact_match),
        "expected_output_match": bool(fitness.expected_output_match),
        "candidate_generated": candidate_count > 0,
        "early_exit": early_exit,
        "true_missing_layer": (not early_exit) and len(genome.branch_path.decisions) < len(sample.get("target_branch_path", [])),
        "early_reject_short_path": early_exit,
        "reject_type": genome.branch_path.reject_type,
        "rejected_by_layer": genome.branch_path.rejected_by_layer,
        "false_reject_supported": bool(sample["supported"] and phenotype.unsupported_pred),
        "false_accept_unsupported": bool((not sample["supported"]) and not phenotype.unsupported_pred),
    }


def _missing_row(sample) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "split": sample["split"],
        "input_mode": sample["input_mode"],
        "expression_family": sample.get("expression_family"),
        "structure_policy": sample.get("structure_policy"),
        "unsupported_reason": sample.get("unsupported_reason"),
        "supported": bool(sample["supported"]),
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": None,
        "unsupported_pred": False,
        "target_ir_exact_match": False,
        "expected_output_match": False,
        "candidate_generated": False,
        "early_exit": False,
        "true_missing_layer": True,
        "early_reject_short_path": False,
        "reject_type": "missing_layer",
        "rejected_by_layer": None,
        "false_reject_supported": False,
        "false_accept_unsupported": not bool(sample["supported"]),
    }


def _metrics_from_rows(rows: List[Dict]) -> Dict:
    return {
        "overall": _aggregate(rows),
        "by_split": _group(rows, "split"),
        "by_input_mode": _group(rows, "input_mode"),
        "by_expression_family": _group(rows, "expression_family"),
        "by_structure_policy": _group(rows, "structure_policy"),
        "by_unsupported_reason": _group(rows, "unsupported_reason"),
        "by_rejected_by_layer": _group(rows, "rejected_by_layer"),
        "by_reject_type": _group(rows, "reject_type"),
        "diagnostics": _diagnostics(rows),
        "rows": rows,
    }


def _group(rows: Iterable[Dict], key: str) -> Dict[str, Dict]:
    buckets = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key))].append(row)
    return {name: _aggregate(bucket) for name, bucket in sorted(buckets.items())}


def _aggregate(rows: List[Dict]) -> Dict:
    sample_count = len(rows)
    supported = [row for row in rows if row["supported"]]
    unsupported = [row for row in rows if not row["supported"]]
    return {
        "sample_count": sample_count,
        "supported_count": len(supported),
        "unsupported_count": len(unsupported),
        "target_ir_exact_match": _rate(supported, "target_ir_exact_match"),
        "expected_output_match": _rate(supported, "expected_output_match"),
        "unsupported_rejection_rate": _rate(unsupported, "unsupported_pred"),
        "false_reject_supported_rate": _rate(supported, "false_reject_supported"),
        "false_accept_unsupported_rate": _rate(unsupported, "false_accept_unsupported"),
        "candidate_generation_success_rate": _rate(rows, "candidate_generated"),
        "true_missing_layer_rate": _rate(rows, "true_missing_layer"),
        "early_reject_short_path_rate": _rate(rows, "early_reject_short_path"),
    }


def _diagnostics(rows: List[Dict]) -> Dict:
    zh_number = [row for row in rows if row["input_mode"] == "zh_number_expression" and row["supported"]]
    unsupported_arithmetic = [row for row in rows if row["input_mode"] == "unsupported_arithmetic"]
    task_scope_rejects = [row for row in rows if row.get("rejected_by_layer") == "task_scope"]
    return {
        "zh_number_expression_false_reject_count": sum(1 for row in zh_number if row["false_reject_supported"]),
        "zh_number_expression_false_reject_rate": _rate(zh_number, "false_reject_supported"),
        "unsupported_arithmetic_false_accept_count": sum(1 for row in unsupported_arithmetic if row["false_accept_unsupported"]),
        "unsupported_arithmetic_false_accept_rate": _rate(unsupported_arithmetic, "false_accept_unsupported"),
        "task_scope_no_confident_reject_count": sum(1 for row in task_scope_rejects if row.get("reject_type") == "no_confident_branch"),
        "arithmetic_family_typed_reject_count": sum(1 for row in rows if row.get("rejected_by_layer") == "arithmetic_family" and row.get("reject_type") == "typed_rejection"),
        "structure_policy_typed_reject_count": sum(1 for row in rows if row.get("rejected_by_layer") == "structure_policy" and row.get("reject_type") == "typed_rejection"),
        "rejected_by_layer_counts": dict(Counter(str(row.get("rejected_by_layer")) for row in rows if row.get("rejected_by_layer"))),
        "reject_type_counts": dict(Counter(str(row.get("reject_type")) for row in rows if row.get("reject_type"))),
    }


def _rate(rows: List[Dict], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)

