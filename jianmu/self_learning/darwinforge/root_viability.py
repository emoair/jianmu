from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ViabilityReport:
    root_id: str
    classification: str
    stable_prefix_length: int
    reproduction_rate: float
    first_wrong_layer: str = ""
    first_confidence_collapse_layer: str = ""
    reason: str = ""

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def diagnose_root_viability(root, perturbation_reproduction_rate: float = 0.0, stable_prefix_threshold: int = 4) -> ViabilityReport:
    stable_len = len(root.stable_prefix)
    first_wrong = root.first_wrong_layer or ""
    collapse = root.first_confidence_collapse_layer or ""
    if root.target_ir_exact_match and stable_len >= stable_prefix_threshold and (not first_wrong or stable_len >= stable_prefix_threshold):
        classification = "undervalued_correct_root" if root.rank > 1 else "alternative_valid_root"
        reason = "correct_with_stable_prefix"
    elif root.target_ir_exact_match and (first_wrong or collapse or stable_len < stable_prefix_threshold):
        if perturbation_reproduction_rate >= 0.5:
            classification = "lucky_correct_root"
            reason = "correct_but_unstable_path"
        else:
            classification = "unstable_correct_root"
            reason = "correct_but_low_reproduction"
    elif root.root_type == "high_score_wrong":
        classification = "high_score_wrong_root"
        reason = "wrong_root_ranked_high"
    else:
        classification = "non_viable_root"
        reason = "no_targetir_nutrient"
    return ViabilityReport(
        root_id=root.root_id,
        classification=classification,
        stable_prefix_length=stable_len,
        reproduction_rate=perturbation_reproduction_rate,
        first_wrong_layer=first_wrong,
        first_confidence_collapse_layer=collapse,
        reason=reason,
    )


def summarize_viability(reports) -> Dict:
    counts = {
        "low_score_correct_count": 0,
        "undervalued_correct_count": 0,
        "lucky_correct_count": 0,
        "unstable_correct_count": 0,
        "alternative_valid_count": 0,
    }
    for report in reports:
        if report.classification in {"undervalued_correct_root", "lucky_correct_root", "unstable_correct_root", "alternative_valid_root"}:
            counts["low_score_correct_count"] += 1
        if report.classification == "undervalued_correct_root":
            counts["undervalued_correct_count"] += 1
        elif report.classification == "lucky_correct_root":
            counts["lucky_correct_count"] += 1
        elif report.classification == "unstable_correct_root":
            counts["unstable_correct_count"] += 1
        elif report.classification == "alternative_valid_root":
            counts["alternative_valid_count"] += 1
    return counts
