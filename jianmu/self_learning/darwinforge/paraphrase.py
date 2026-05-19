from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

from jianmu.self_learning.darwinforge.candidate import CandidateRecord


@dataclass
class ParaphraseGroup:
    group_id: str
    samples: List[Dict]
    target_ir_canonical: Optional[str]
    expected_output: Optional[str]
    supported: bool
    input_modes: List[str]

    def to_dict(self) -> Dict:
        return {
            "group_id": self.group_id,
            "sample_ids": [sample["sample_id"] for sample in self.samples],
            "target_ir_canonical": self.target_ir_canonical,
            "expected_output": self.expected_output,
            "supported": self.supported,
            "input_modes": list(self.input_modes),
        }


@dataclass
class ParaphrasePredictionGroup:
    group_id: str
    records: List[CandidateRecord]
    predicted_targetirs: List[Optional[str]]
    rejected_count: int
    accepted_count: int

    def to_dict(self) -> Dict:
        return {
            "group_id": self.group_id,
            "predicted_targetirs": list(self.predicted_targetirs),
            "rejected_count": self.rejected_count,
            "accepted_count": self.accepted_count,
        }


def group_dataset_by_paraphrase(samples: List[Dict]) -> Dict[str, ParaphraseGroup]:
    buckets: Dict[str, List[Dict]] = defaultdict(list)
    for sample in samples:
        buckets[sample["paraphrase_group"]].append(sample)
    groups = {}
    for group_id, group_samples in buckets.items():
        supported = all(sample["supported"] for sample in group_samples)
        target_values = {sample.get("target_ir_canonical") for sample in group_samples if sample.get("target_ir_canonical")}
        output_values = {sample.get("expected_output") for sample in group_samples if sample.get("expected_output")}
        if supported and len(target_values) != 1:
            raise ValueError(f"supported paraphrase group has inconsistent TargetIR: {group_id}")
        if supported and len(output_values) != 1:
            raise ValueError(f"supported paraphrase group has inconsistent expected output: {group_id}")
        groups[group_id] = ParaphraseGroup(
            group_id=group_id,
            samples=group_samples,
            target_ir_canonical=next(iter(target_values)) if target_values else None,
            expected_output=next(iter(output_values)) if output_values else None,
            supported=supported,
            input_modes=sorted({sample.get("input_mode", "") for sample in group_samples}),
        )
    return groups


def group_predictions_by_paraphrase(records: List[CandidateRecord], samples: List[Dict]) -> Dict[str, ParaphrasePredictionGroup]:
    buckets: Dict[str, List[CandidateRecord]] = defaultdict(list)
    for record, sample in zip(records, samples):
        buckets[sample["paraphrase_group"]].append(record)
    result = {}
    for group_id, group_records in buckets.items():
        predicted = [record.phenotype.target_ir_canonical for record in group_records]
        rejected = sum(1 for record in group_records if record.phenotype.unsupported_pred)
        result[group_id] = ParaphrasePredictionGroup(
            group_id=group_id,
            records=group_records,
            predicted_targetirs=predicted,
            rejected_count=rejected,
            accepted_count=len(group_records) - rejected,
        )
    return result


def compute_group_metrics(records: List[CandidateRecord], samples: List[Dict]) -> Dict:
    dataset_groups = group_dataset_by_paraphrase(samples)
    prediction_groups = group_predictions_by_paraphrase(records, samples)
    supported_groups = [group for group in dataset_groups.values() if group.supported]
    ood_samples = [sample for sample in samples if sample.get("input_mode", "").startswith("ood_")]
    group_consistent = 0
    group_exact = 0
    cross_mode_consistent = 0
    supported_all_rejected = 0
    inconsistent = 0
    representative = []
    outputs_by_group = {}
    for group in supported_groups:
        prediction = prediction_groups.get(group.group_id)
        accepted_targetirs = [
            record.phenotype.target_ir_canonical
            for record in prediction.records
            if not record.phenotype.unsupported_pred and record.phenotype.target_ir_canonical
        ] if prediction else []
        all_rejected = bool(prediction) and prediction.rejected_count == len(group.samples)
        if all_rejected or not accepted_targetirs:
            supported_all_rejected += 1
            consistent = False
        else:
            consistent = len(set(accepted_targetirs)) == 1
        exact = bool(prediction) and all(
            (not record.phenotype.unsupported_pred) and record.phenotype.target_ir_canonical == group.target_ir_canonical
            for record in prediction.records
        )
        by_mode = defaultdict(set)
        if prediction:
            for record, sample in zip(prediction.records, group.samples):
                if not record.phenotype.unsupported_pred and record.phenotype.target_ir_canonical:
                    by_mode[sample.get("input_mode")].add(record.phenotype.target_ir_canonical)
        cross_consistent = bool(by_mode) and len(by_mode) >= 2 and len(set().union(*by_mode.values())) == 1
        group_consistent += int(consistent)
        group_exact += int(exact)
        cross_mode_consistent += int(cross_consistent)
        inconsistent += int(not consistent and not all_rejected)
        outputs_by_group[group.group_id] = accepted_targetirs[0] if accepted_targetirs and len(set(accepted_targetirs)) == 1 else None
        representative.append(
            {
                "group_id": group.group_id,
                "target_ir": group.target_ir_canonical,
                "predicted_targetirs": accepted_targetirs,
                "consistent": consistent,
                "exact": exact,
                "input_modes": group.input_modes,
            }
        )
    collapse_rate = _collapse_rate(outputs_by_group, {group.group_id: group.target_ir_canonical for group in supported_groups})
    ood_rejected = 0
    ood_false_accept = 0
    for record, sample in zip(records, samples):
        if sample not in ood_samples:
            continue
        if record.phenotype.unsupported_pred:
            ood_rejected += 1
        else:
            ood_false_accept += 1
    supported_den = max(len(supported_groups), 1)
    ood_den = max(len(ood_samples), 1)
    return {
        "sample_target_ir_exact_match": round(sum(1 for record in records if record.fitness_report.target_ir_exact_match) / max(len(samples), 1), 4),
        "group_targetir_consistency": round(group_consistent / supported_den, 4),
        "group_targetir_exact_match": round(group_exact / supported_den, 4),
        "cross_mode_consistency": round(cross_mode_consistent / supported_den, 4),
        "paraphrase_collapse_rate": collapse_rate,
        "ood_rejection_rate": round(ood_rejected / ood_den, 4),
        "ood_false_accept_rate": round(ood_false_accept / ood_den, 4),
        "supported_all_rejected_group_count": supported_all_rejected,
        "group_inconsistent_count": inconsistent,
        "supported_group_count": len(supported_groups),
        "ood_count": len(ood_samples),
        "representative_group_predictions": representative[:8],
    }


def apply_group_fitness(records: List[CandidateRecord], samples: List[Dict]) -> Dict:
    metrics = compute_group_metrics(records, samples)
    dataset_groups = group_dataset_by_paraphrase(samples)
    prediction_groups = group_predictions_by_paraphrase(records, samples)
    for group_id, group in dataset_groups.items():
        prediction = prediction_groups.get(group_id)
        if not prediction:
            continue
        if not group.supported:
            for record in prediction.records:
                delta = 1.0 if record.phenotype.unsupported_pred else -3.0
                _adjust_fitness(record, delta, "ood_group_rejection_feedback")
            continue
        accepted = [record for record in prediction.records if not record.phenotype.unsupported_pred and record.phenotype.target_ir_canonical]
        if not accepted:
            for record in prediction.records:
                _adjust_fitness(record, -1.5, "group_all_rejected_when_supported")
            continue
        predicted_values = {record.phenotype.target_ir_canonical for record in accepted}
        exact_records = [record for record in prediction.records if record.phenotype.target_ir_canonical == group.target_ir_canonical]
        if len(predicted_values) == 1:
            for record in accepted:
                _adjust_fitness(record, 1.0, "group_targetir_consistency")
        else:
            for record in prediction.records:
                _adjust_fitness(record, -1.0, "inconsistent_targetir_within_group")
        if len(exact_records) == len(group.samples):
            for record in exact_records:
                _adjust_fitness(record, 2.0, "group_targetir_exact_match")
        elif predicted_values and group.target_ir_canonical not in predicted_values:
            for record in accepted:
                _adjust_fitness(record, -2.0, "paraphrase_wrong_consistent_or_inexact")
        if _cross_mode_exact(prediction.records, group.samples, group.target_ir_canonical):
            for record in prediction.records:
                _adjust_fitness(record, 1.0, "cross_mode_consistency")
    return metrics


def _adjust_fitness(record: CandidateRecord, delta: float, component: str):
    record.fitness_report.total_fitness = round(record.fitness_report.total_fitness + delta, 4)
    record.fitness_report.components[component] = round(record.fitness_report.components.get(component, 0.0) + delta, 4)


def _cross_mode_exact(records: List[CandidateRecord], samples: List[Dict], target_ir: str) -> bool:
    modes = defaultdict(list)
    for record, sample in zip(records, samples):
        modes[sample.get("input_mode")].append(record)
    if len(modes) < 2:
        return False
    return all(
        all((not record.phenotype.unsupported_pred) and record.phenotype.target_ir_canonical == target_ir for record in mode_records)
        for mode_records in modes.values()
    )


def _collapse_rate(outputs_by_group: Dict[str, Optional[str]], target_by_group: Dict[str, Optional[str]]) -> float:
    predicted_to_groups = defaultdict(list)
    for group_id, predicted in outputs_by_group.items():
        if predicted:
            predicted_to_groups[predicted].append(group_id)
    collapsed = 0
    for predicted, group_ids in predicted_to_groups.items():
        if len(group_ids) <= 1:
            continue
        wrong_groups = [group_id for group_id in group_ids if target_by_group.get(group_id) != predicted]
        collapsed += len(wrong_groups)
    return round(collapsed / max(len(target_by_group), 1), 4)
