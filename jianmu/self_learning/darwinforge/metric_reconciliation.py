from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


OOD_REJECT_LAYERS = {
    "task_scope",
    "language_target",
    "support_gate",
    "arithmetic_family",
    "structure_policy",
}


@dataclass
class MetricScope:
    split: str
    sample_count: int
    evaluator_name: str
    guard_state: str
    population_state: str
    scale_label: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def evaluate_ood_rows(rows: List[Dict], scope: MetricScope) -> Dict:
    unsupported = [row for row in rows if not row.get("supported")]
    false_accept = [row for row in unsupported if _false_accept(row)]
    rejected = [row for row in unsupported if not _false_accept(row)]
    return {
        **scope.to_dict(),
        "ood_sample_count": len(unsupported),
        "ood_rejection_rate": _rate(len(unsupported), len(rejected)),
        "ood_false_accept_rate": _rate(len(unsupported), len(false_accept)),
        "false_accept_count": len(false_accept),
        "rejection_count": len(rejected),
    }


def summarize_global_rows(rows: List[Dict], scope: MetricScope) -> Dict:
    supported = [row for row in rows if row.get("supported")]
    unsupported = [row for row in rows if not row.get("supported")]
    ood = evaluate_ood_rows(rows, scope)
    return {
        **scope.to_dict(),
        "sample_count": len(rows),
        "supported_count": len(supported),
        "unsupported_count": len(unsupported),
        "global_correct_targetir_in_beam_rate": _rate(len(supported), sum(1 for row in supported if row.get("correct_targetir_in_beam"))),
        "candidate_space_failure_rate": _rate(len(supported), sum(1 for row in supported if row.get("candidate_space_failure"))),
        "target_ir_exact_match_beam_oracle": _rate(len(supported), sum(1 for row in supported if row.get("best_beam_exact"))),
        "ood_rejection_rate": ood["ood_rejection_rate"],
        "ood_false_accept_rate": ood["ood_false_accept_rate"],
    }


def reconcile_metrics(main_metrics: Dict, scale_metrics: Iterable[Dict]) -> Dict:
    inconsistent = []
    main_ood = main_metrics.get("ood_false_accept_after", main_metrics.get("ood_false_accept_rate"))
    main_count = main_metrics.get("ood_sample_count")
    for row in scale_metrics:
        if row.get("skipped"):
            continue
        if main_count is not None and row.get("ood_sample_count") not in {None, main_count}:
            continue
        if "ood_false_accept_rate" in row and main_ood is not None and abs(row["ood_false_accept_rate"] - main_ood) > 0.0001:
            inconsistent.append(f"ood_false_accept_rate:{row.get('scale_label', row.get('scale'))}")
    return {
        "metric_consistency_passed": not inconsistent,
        "inconsistent_metric_names": inconsistent,
        "ood_metric_consistency_passed": not any(name.startswith("ood_") for name in inconsistent),
        "scale_metric_consistency_passed": not inconsistent,
    }


def _false_accept(row: Dict) -> bool:
    if row.get("false_accept_unsupported") is not None:
        return bool(row.get("false_accept_unsupported"))
    if row.get("unsupported_pred") is not None:
        return not bool(row.get("unsupported_pred"))
    rejected = row.get("rejected_by_layer") in OOD_REJECT_LAYERS or row.get("reject_type") in {"no_confident_branch", "typed_rejection"}
    return not rejected


def _rate(denominator: int, numerator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator, 4)
