from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NutrientSignal:
    target_ir_nutrient: float = 0.0
    expected_output_nutrient: float = 0.0
    compiler_nutrient: float = 0.0
    ood_rejection_nutrient: float = 0.0
    path_confidence_alignment: float = 0.0

    @property
    def total_nutrient(self) -> float:
        return round(
            self.target_ir_nutrient
            + self.expected_output_nutrient
            + self.compiler_nutrient
            + self.ood_rejection_nutrient
            + self.path_confidence_alignment,
            4,
        )

    def to_dict(self) -> Dict:
        return {
            "target_ir_nutrient": self.target_ir_nutrient,
            "expected_output_nutrient": self.expected_output_nutrient,
            "compiler_nutrient": self.compiler_nutrient,
            "ood_rejection_nutrient": self.ood_rejection_nutrient,
            "path_confidence_alignment": self.path_confidence_alignment,
            "total_nutrient": self.total_nutrient,
        }


@dataclass
class RootCandidate:
    root_id: str
    sample_id: str
    raw_text: str
    canonical_text: str
    branch_path: object
    phenotype: object
    fitness: object
    rank: int
    target_ir_exact_match: bool
    expected_output_match: bool
    unsupported_correct: bool
    nutrient_score: float
    root_type: str
    stable_prefix: List[List[str]] = field(default_factory=list)
    first_confidence_collapse_layer: Optional[str] = None
    first_wrong_layer: Optional[str] = None
    regrowth_fork_point: Optional[str] = None
    necrosis_state: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "root_id": self.root_id,
            "sample_id": self.sample_id,
            "raw_text": self.raw_text,
            "canonical_text": self.canonical_text,
            "branch_path": self.branch_path.to_dict() if hasattr(self.branch_path, "to_dict") else self.branch_path,
            "phenotype": self.phenotype.to_dict() if hasattr(self.phenotype, "to_dict") else self.phenotype,
            "fitness": self.fitness.to_dict() if hasattr(self.fitness, "to_dict") else self.fitness,
            "rank": self.rank,
            "target_ir_exact_match": self.target_ir_exact_match,
            "expected_output_match": self.expected_output_match,
            "unsupported_correct": self.unsupported_correct,
            "nutrient_score": self.nutrient_score,
            "root_type": self.root_type,
            "stable_prefix": list(self.stable_prefix),
            "first_confidence_collapse_layer": self.first_confidence_collapse_layer,
            "first_wrong_layer": self.first_wrong_layer,
            "regrowth_fork_point": self.regrowth_fork_point,
            "necrosis_state": self.necrosis_state,
        }


@dataclass
class RootMemory:
    stable_root_buffer: List[RootCandidate] = field(default_factory=list)
    undervalued_correct_buffer: List[RootCandidate] = field(default_factory=list)
    high_score_wrong_buffer: List[RootCandidate] = field(default_factory=list)
    necrosis_queue: List[RootCandidate] = field(default_factory=list)
    regrowth_queue: List[RootCandidate] = field(default_factory=list)
    hard_case_buffer: List[Dict] = field(default_factory=list)

    def summary(self) -> Dict:
        return {
            "stable_root_buffer": len(self.stable_root_buffer),
            "undervalued_correct_buffer": len(self.undervalued_correct_buffer),
            "high_score_wrong_buffer": len(self.high_score_wrong_buffer),
            "necrosis_queue": len(self.necrosis_queue),
            "regrowth_queue": len(self.regrowth_queue),
            "hard_case_buffer": len(self.hard_case_buffer),
        }


def nutrient_from_record(record, supported: bool) -> NutrientSignal:
    return NutrientSignal(
        target_ir_nutrient=4.0 if getattr(record.fitness_report, "target_ir_exact_match", False) else 0.0,
        expected_output_nutrient=2.0 if getattr(record.fitness_report, "expected_output_match", False) else 0.0,
        compiler_nutrient=1.0 if getattr(record.fitness_report, "compile_success", False) else 0.0,
        ood_rejection_nutrient=2.0 if (not supported and record.phenotype.unsupported_pred) else 0.0,
        path_confidence_alignment=_confidence_alignment(record.genome.branch_path),
    )


def root_candidate_from_record(sample: Dict, record, rank: int, canonical_text: str, diagnostic: Dict = None) -> RootCandidate:
    diagnostic = diagnostic or {}
    nutrient = nutrient_from_record(record, bool(sample.get("supported")))
    root_type = classify_root_type(record, bool(sample.get("supported")), rank)
    decisions = [[decision.layer_name, decision.selected] for decision in record.genome.branch_path.decisions]
    return RootCandidate(
        root_id=f"{sample.get('sample_id')}:{record.genome.genome_id}:{rank}",
        sample_id=sample.get("sample_id", ""),
        raw_text=sample.get("input_text", ""),
        canonical_text=canonical_text,
        branch_path=record.genome.branch_path,
        phenotype=record.phenotype,
        fitness=record.fitness_report,
        rank=rank,
        target_ir_exact_match=bool(record.fitness_report.target_ir_exact_match),
        expected_output_match=bool(record.fitness_report.expected_output_match),
        unsupported_correct=bool(record.fitness_report.unsupported_correct),
        nutrient_score=nutrient.total_nutrient,
        root_type=root_type,
        stable_prefix=stable_prefix_from_decisions(record.genome.branch_path.decisions),
        first_confidence_collapse_layer=first_confidence_collapse_layer(record.genome.branch_path.decisions),
        first_wrong_layer=diagnostic.get("first_wrong_layer"),
        regrowth_fork_point=diagnostic.get("first_wrong_layer"),
        necrosis_state=None,
    )


def classify_root_type(record, supported: bool, rank: int) -> str:
    exact = bool(record.fitness_report.target_ir_exact_match)
    wrong = supported and not exact
    if exact and rank == 1:
        return "high_score_correct"
    if wrong and rank == 1:
        return "high_score_wrong"
    if exact:
        return "low_score_correct"
    if record.phenotype.unsupported_pred:
        return "rejected_root"
    if not supported and not record.phenotype.unsupported_pred:
        return "high_score_wrong" if rank == 1 else "low_score_wrong"
    return "candidate_space_failure" if supported else "low_score_wrong"


def stable_prefix_from_decisions(decisions, min_confidence: int = 20) -> List[List[str]]:
    prefix: List[List[str]] = []
    for decision in decisions:
        if decision.confidence < min_confidence:
            break
        prefix.append([decision.layer_name, decision.selected])
    return prefix


def first_confidence_collapse_layer(decisions, drop: int = 20) -> Optional[str]:
    previous = None
    for decision in decisions:
        if previous is not None and previous - decision.confidence >= drop:
            return decision.layer_name
        previous = decision.confidence
    return None


def nutrient_contrast(positive: RootCandidate, negative: RootCandidate, margin: float = 1.0) -> Dict:
    positive_score = positive.nutrient_score
    negative_score = negative.nutrient_score
    adjustment = max(0.0, margin - (positive_score - negative_score))
    return {
        "positive_root_id": positive.root_id,
        "negative_root_id": negative.root_id,
        "margin": margin,
        "positive_score": positive_score,
        "negative_score": negative_score,
        "contrast_bonus": round(adjustment, 4),
        "contrast_penalty": round(adjustment, 4),
        "satisfied": positive_score > negative_score + margin,
    }


def _confidence_alignment(branch_path) -> float:
    if not branch_path.decisions:
        return 0.0
    return round(sum(decision.confidence for decision in branch_path.decisions) / (100.0 * len(branch_path.decisions)), 4)
