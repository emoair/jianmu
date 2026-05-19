from collections import Counter, defaultdict
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.fitness import compute_fitness


def evaluate_symbol_grounding(population, samples: List[Dict], top_k: int = 5, sample_limit: Optional[int] = None) -> Dict:
    """Symbol Grounding（符号接地） evaluation using labels only after prediction."""
    selected = list(samples[:sample_limit] if sample_limit is not None else samples)
    synthesis = AtomicSynthesis()
    rows = []
    for sample in selected:
        features = extract_surface_features(sample["input_text"])
        genomes = population.sample_candidate_paths(features, top_k=top_k)
        if not genomes:
            rows.append(_missing_row(sample))
            continue
        best = None
        for genome in genomes:
            phenotype = synthesis.synthesize(genome, features)
            fitness = compute_fitness(genome, phenotype, sample, sandbox_optional=False)
            record = (fitness.total_fitness, genome, phenotype, fitness)
            if best is None or record[0] > best[0]:
                best = record
        _, genome, phenotype, fitness = best
        rows.append(_row(sample, genome, phenotype, fitness))
    metrics = {
        "overall": _aggregate(rows),
        "symbol_metrics": _symbol_metrics(rows),
        "by_curriculum_stage": _group(rows, "curriculum_stage"),
        "by_input_mode": _group(rows, "input_mode"),
        "rows": rows,
    }
    return metrics


def _row(sample, genome, phenotype, fitness) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "paired_group_id": sample["paired_group_id"],
        "curriculum_stage": sample["curriculum_stage"],
        "input_mode": sample["input_mode"],
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": phenotype.target_ir_canonical,
        "unsupported_pred": phenotype.unsupported_pred,
        "target_ir_exact_match": fitness.target_ir_exact_match,
        "expected_output_match": fitness.expected_output_match,
        "false_reject_supported": bool(sample["supported"] and phenotype.unsupported_pred),
        "false_accept_unsupported": bool((not sample["supported"]) and not phenotype.unsupported_pred),
        "task_scope_continued": any(decision.layer_name == "task_scope" and decision.selected == "programming" for decision in genome.branch_path.decisions),
        "symbol_slots": sample.get("symbol_slots", []),
        "operator_slots": sample.get("operator_slots", []),
    }


def _missing_row(sample) -> Dict:
    return {
        "sample_id": sample["sample_id"],
        "paired_group_id": sample["paired_group_id"],
        "curriculum_stage": sample["curriculum_stage"],
        "input_mode": sample["input_mode"],
        "supported": sample["supported"],
        "target_ir_true": sample.get("target_ir_canonical"),
        "target_ir_pred": None,
        "unsupported_pred": False,
        "target_ir_exact_match": False,
        "expected_output_match": False,
        "false_reject_supported": False,
        "false_accept_unsupported": not sample["supported"],
        "task_scope_continued": False,
        "symbol_slots": sample.get("symbol_slots", []),
        "operator_slots": sample.get("operator_slots", []),
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


def _symbol_metrics(rows: List[Dict]) -> Dict:
    zh_rows = [row for row in rows if row["input_mode"] == "zh_number_expression" and row["supported"]]
    supported = [row for row in rows if row["supported"]]
    numeral_slots = []
    operator_slots = []
    for row in supported:
        for slot in row.get("symbol_slots", []):
            numeral_slots.append((row, slot))
        for slot in row.get("operator_slots", []):
            operator_slots.append((row, slot))
    numeral_correct = sum(1 for row, slot in numeral_slots if row.get("target_ir_pred") and f"lit({slot['target_literal']})" in row["target_ir_pred"])
    operator_correct = sum(1 for row, slot in operator_slots if row.get("target_ir_pred") and slot["target_operator"] in row["target_ir_pred"])
    paired = _paired_agreement(rows)
    return {
        "zh_number_expression_false_reject_rate": _rate(zh_rows, "false_reject_supported"),
        "zh_number_task_scope_continue_rate": _rate(zh_rows, "task_scope_continued"),
        "zh_number_targetir_exact_match": _rate(zh_rows, "target_ir_exact_match"),
        "symbol_slot_accuracy": round((numeral_correct + operator_correct) / max(len(numeral_slots) + len(operator_slots), 1), 4),
        "numeral_slot_accuracy": round(numeral_correct / max(len(numeral_slots), 1), 4),
        "operator_slot_accuracy": round(operator_correct / max(len(operator_slots), 1), 4),
        "paired_arabic_zh_agreement": paired["paired_arabic_zh_agreement"],
        "paired_group_targetir_consistency": paired["paired_group_targetir_consistency"],
    }


def _paired_agreement(rows: List[Dict]) -> Dict:
    groups = defaultdict(list)
    for row in rows:
        if row["supported"]:
            groups[row["paired_group_id"]].append(row)
    agreement_count = 0
    consistency_count = 0
    considered = 0
    for group_rows in groups.values():
        arabic = [row for row in group_rows if row["input_mode"] == "arabic_math_expression"]
        zh = [row for row in group_rows if row["input_mode"] == "zh_number_expression"]
        preds = [row["target_ir_pred"] for row in group_rows if row["target_ir_pred"]]
        if preds:
            considered += 1
            consistency_count += int(len(set(preds)) == 1)
        if arabic and zh:
            agreement_count += int(arabic[0]["target_ir_pred"] is not None and arabic[0]["target_ir_pred"] == zh[0]["target_ir_pred"])
    pairable = sum(1 for group_rows in groups.values() if {row["input_mode"] for row in group_rows} >= {"arabic_math_expression", "zh_number_expression"})
    return {
        "paired_arabic_zh_agreement": round(agreement_count / max(pairable, 1), 4),
        "paired_group_targetir_consistency": round(consistency_count / max(considered, 1), 4),
    }


def _group(rows: List[Dict], key: str) -> Dict[str, Dict]:
    buckets = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key))].append(row)
    return {name: _aggregate(bucket) for name, bucket in sorted(buckets.items())}


def _rate(rows: List[Dict], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for row in rows if row.get(key)) / len(rows), 4)

