from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class AssimilationRecord:
    sample_id: str
    raw_text: str
    canonical_text: str
    rescued_by_subbeam: bool
    subbeam_path: List[List[str]]
    global_top1_path: List[List[str]]
    fork_layer: str
    rescued_target_ir: Optional[str]
    target_ir_exact_match: bool
    rescued_path_rank: Optional[int]
    global_failure_reason: Optional[str]
    assimilation_updates: List[Dict] = field(default_factory=list)
    applied: bool = False
    split: str = "train"

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def extract_assimilation_records(subbeam_results: Iterable, router_score_diagnostics: List[Dict], samples: List[Dict] = None) -> List[AssimilationRecord]:
    """Extract RootFork Global Assimilation（根叉全局吸收） records from train sub-beam rescues."""

    sample_by_id = {sample.get("sample_id"): sample for sample in samples or []}
    score_by_id = {row.get("sample_id"): row for row in router_score_diagnostics}
    records = []
    for result in subbeam_results:
        payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        sample = sample_by_id.get(payload.get("sample_id"), {})
        if sample and sample.get("split", "train") != "train":
            records.append(_skipped_record(payload, sample, "non_train_split"))
            continue
        if not payload.get("correct_targetir_in_subbeam"):
            continue
        score_diag = score_by_id.get(payload.get("sample_id"), {}).get("score_diagnostic", {})
        path = _best_path(payload)
        updates = _updates_from_path(path, sample, score_diag)
        records.append(
            AssimilationRecord(
                sample_id=payload.get("sample_id", ""),
                raw_text=sample.get("input_text", payload.get("raw_text", "")),
                canonical_text=payload.get("canonical_text", sample.get("input_text", "")),
                rescued_by_subbeam=True,
                subbeam_path=path,
                global_top1_path=[],
                fork_layer=payload.get("fork_layer", ""),
                rescued_target_ir=payload.get("subbeam_best_targetir"),
                target_ir_exact_match=bool(payload.get("subbeam_best_exact", payload.get("correct_targetir_in_subbeam"))),
                rescued_path_rank=payload.get("first_success_rank"),
                global_failure_reason=payload.get("fork_reason"),
                assimilation_updates=updates,
                split=sample.get("split", "train"),
            )
        )
    return records


def apply_global_assimilation(population, assimilation_records: Iterable[AssimilationRecord], strength: int = 2) -> Dict:
    records = list(assimilation_records)
    updated_layers = Counter()
    updated_options = Counter()
    weight_delta = Counter()
    skipped_eval = 0
    skipped_ood = 0
    applied_count = 0
    for record in records:
        if record.split == "eval":
            skipped_eval += 1
            continue
        if record.split == "ood":
            skipped_ood += 1
            continue
        record.applied = True
        applied_count += 1
        for update in record.assimilation_updates:
            layer = update["layer_name"]
            option = update["option"]
            for neuron in population.per_layer.get(layer, []):
                if neuron.option != option:
                    continue
                for name, delta in update.get("weight_updates", {}).items():
                    applied_delta = int(delta * strength)
                    neuron.weights[name] = neuron.weights.get(name, 0) + applied_delta
                    weight_delta[name] += applied_delta
                neuron.score_value += 0.5 * strength
                updated_layers[layer] += 1
                updated_options[f"{layer}={option}"] += 1
    return {
        "assimilation_record_count": len([record for record in records if record.rescued_by_subbeam and record.split == "train"]),
        "rescued_path_assimilation_count": applied_count,
        "branch_neuron_updated_count": sum(updated_layers.values()),
        "updated_layer_distribution": dict(updated_layers),
        "updated_option_distribution": dict(updated_options),
        "weight_delta_summary": dict(weight_delta),
        "skipped_eval_records_count": skipped_eval,
        "skipped_ood_records_count": skipped_ood,
    }


def _updates_from_path(path: List[List[str]], sample: Dict, score_diag: Dict) -> List[Dict]:
    updates = []
    focus_layers = {"slot_binding_policy", "arithmetic_family", "structure_policy", "target_builder"}
    for layer, option in path:
        if layer not in focus_layers:
            continue
        weights = _generic_weight_updates(layer, option, sample)
        if layer == "slot_binding_policy":
            weights.update(_slot_binding_updates(option, sample))
        if weights:
            updates.append({"layer_name": layer, "option": option, "weight_updates": weights})
    return updates


def _best_path(payload: Dict) -> List[List[str]]:
    summaries = payload.get("generated_paths_summary", [])
    if not summaries:
        return []
    exact = next((row for row in summaries if row.get("target_ir_pred") == payload.get("subbeam_best_targetir")), summaries[0])
    return exact.get("decisions", [])


def _generic_weight_updates(layer: str, option: str, sample: Dict) -> Dict:
    updates = {}
    if sample.get("number_count"):
        updates["number_count"] = 1
    if sample.get("operator_count"):
        updates["operator_count"] = 1
    if sample.get("structure_policy") == "literal_value":
        updates["signed_literal_only"] = 2
    if sample.get("structure_policy") == "precedence_tree":
        updates["operator_count"] = max(updates.get("operator_count", 0), 2)
    if sample.get("has_parentheses") or sample.get("structure_policy") == "parenthesized_tree":
        updates["contains_parentheses"] = 2
    if sample.get("input_mode") in {"zh_number_expression", "paired_zh_natural", "mixed_zh_arabic"}:
        updates["canonical_changed"] = 1
    return updates


def _slot_binding_updates(option: str, sample: Dict) -> Dict:
    if option == "surface_number_order":
        return {"number_count": 4, "operator_count": 2, "input_mode_guess_math_expression": 2}
    if option == "signed_number_order":
        return {"has_negative": 5, "signed_literal_only": 4, "binary_minus_present": 2}
    if option == "chinese_number_order":
        return {"contains_canonicalized_zh_number": 2, "canonical_changed": 2}
    return {}


def _skipped_record(payload: Dict, sample: Dict, reason: str) -> AssimilationRecord:
    return AssimilationRecord(
        sample_id=payload.get("sample_id", ""),
        raw_text=sample.get("input_text", ""),
        canonical_text=sample.get("input_text", ""),
        rescued_by_subbeam=False,
        subbeam_path=[],
        global_top1_path=[],
        fork_layer=payload.get("fork_layer", ""),
        rescued_target_ir=None,
        target_ir_exact_match=False,
        rescued_path_rank=None,
        global_failure_reason=reason,
        split=sample.get("split", "eval"),
    )
