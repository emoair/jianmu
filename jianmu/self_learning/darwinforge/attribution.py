from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_chain import decision_pairs


@dataclass
class LayerAttribution:
    layer_name: str
    error_type: str
    severity: float
    detail: str

    def to_dict(self) -> Dict:
        return {
            "layer_name": self.layer_name,
            "error_type": self.error_type,
            "severity": self.severity,
            "detail": self.detail,
        }


def attribute_candidate_error(record, target: Dict) -> List[LayerAttribution]:
    attrs: List[LayerAttribution] = []
    pred_pairs = decision_pairs(record.genome.branch_path)
    target_pairs = target.get("target_branch_path", [])
    for layer, expected in target_pairs:
        actual = next((value for name, value in pred_pairs if name == layer), None)
        if actual is None:
            attrs.append(LayerAttribution(layer, "missing_layer", 0.8, f"expected {expected}"))
        elif actual != expected:
            severity = 1.0 if layer in {"support_gate", "target_builder"} else 0.6
            error_type = "support_gate_high_severity" if layer == "support_gate" else "target_builder_high_severity" if layer == "target_builder" else "wrong_branch"
            attrs.append(LayerAttribution(layer, error_type, severity, f"{actual} != {expected}"))
    if not attrs and target.get("supported") and not record.fitness_report.target_ir_exact_match:
        attrs.append(LayerAttribution("target_builder", "atomic_synthesis_error", 0.7, "branch path matched but TargetIR differed"))
    return attrs


def aggregate_hard_case_attribution(records, targets_by_input: Dict) -> Dict[str, Dict]:
    totals = Counter()
    severity = defaultdict(float)
    for record in records:
        target = targets_by_input.get(record.genome.genome_id) or targets_by_input.get(record.phenotype.genome_id)
        if target is None:
            target = getattr(record, "target", None)
        if target is None:
            continue
        attrs = attribute_candidate_error(record, target)
        for attr in attrs:
            totals[attr.layer_name] += 1
            severity[attr.layer_name] += attr.severity
    total_records = max(len(records), 1)
    return {
        layer: {
            "error_count": count,
            "error_rate": round(count / total_records, 4),
            "severity": round(severity[layer] / total_records, 4),
        }
        for layer, count in totals.items()
    }

