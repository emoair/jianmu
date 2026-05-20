from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PathDiagnosticRecord:
    sample_id: str
    raw_text: str
    canonical_text: str
    supported: bool
    target_ir_true: Optional[str]
    target_branch_path_true: List
    path_count: int
    complete_path_count: int
    top1_target_ir_pred: Optional[str]
    top1_exact: bool
    best_beam_target_ir_pred: Optional[str]
    best_beam_exact: bool
    correct_targetir_in_beam: bool
    correct_path_in_beam: bool
    correct_targetir_rank: Optional[int]
    correct_path_rank: Optional[int]
    top1_wrong_but_correct_in_beam: bool
    candidate_space_failure: bool
    ranking_failure: bool
    upstream_boundary_failure: bool
    synthesis_failure: bool
    first_wrong_layer: Optional[str]
    first_wrong_expected: Optional[str]
    first_wrong_actual: Optional[str]
    rejected_by_layer: Optional[str]
    source_clone_ids_used: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def diagnose_paths(sample: Dict, candidate_records: List, canonical_text: str = "") -> PathDiagnosticRecord:
    ranked = sorted(candidate_records, key=lambda record: record.fitness_report.total_fitness, reverse=True)
    top1 = ranked[0] if ranked else None
    target_ir = sample.get("target_ir_canonical")
    target_path = sample.get("target_branch_path", [])
    exact_records = [record for record in ranked if record.phenotype.target_ir_canonical == target_ir and sample.get("supported")]
    path_records = [record for record in ranked if _path_matches(record.genome.branch_path.decisions, target_path)]
    first_wrong = _first_wrong(top1.genome.branch_path.decisions if top1 else [], target_path)
    correct_rank = ranked.index(exact_records[0]) + 1 if exact_records else None
    correct_path_rank = ranked.index(path_records[0]) + 1 if path_records else None
    complete_count = sum(1 for record in ranked if not record.genome.branch_path.early_exit)
    correct_targetir_in_beam = bool(exact_records)
    correct_path_in_beam = bool(path_records)
    top1_exact = bool(top1 and top1.phenotype.target_ir_canonical == target_ir and sample.get("supported"))
    candidate_space_failure = bool(sample.get("supported") and not correct_targetir_in_beam)
    ranking_failure = bool(correct_targetir_in_beam and not top1_exact)
    synthesis_failure = bool(correct_path_in_beam and not correct_targetir_in_beam)
    return PathDiagnosticRecord(
        sample_id=sample.get("sample_id", ""),
        raw_text=sample.get("input_text", ""),
        canonical_text=canonical_text,
        supported=bool(sample.get("supported")),
        target_ir_true=target_ir,
        target_branch_path_true=target_path,
        path_count=len(ranked),
        complete_path_count=complete_count,
        top1_target_ir_pred=top1.phenotype.target_ir_canonical if top1 else None,
        top1_exact=top1_exact,
        best_beam_target_ir_pred=exact_records[0].phenotype.target_ir_canonical if exact_records else (top1.phenotype.target_ir_canonical if top1 else None),
        best_beam_exact=bool(exact_records),
        correct_targetir_in_beam=correct_targetir_in_beam,
        correct_path_in_beam=correct_path_in_beam,
        correct_targetir_rank=correct_rank,
        correct_path_rank=correct_path_rank,
        top1_wrong_but_correct_in_beam=bool(correct_targetir_in_beam and not top1_exact),
        candidate_space_failure=candidate_space_failure,
        ranking_failure=ranking_failure,
        upstream_boundary_failure=bool(candidate_space_failure and first_wrong[0] in {"task_scope", "language_target", "semantic_domain", "support_gate"}),
        synthesis_failure=synthesis_failure,
        first_wrong_layer=first_wrong[0],
        first_wrong_expected=first_wrong[1],
        first_wrong_actual=first_wrong[2],
        rejected_by_layer=top1.genome.branch_path.rejected_by_layer if top1 else None,
        source_clone_ids_used=sorted({decision.evidence.get("source_clone_id", "base") for record in ranked for decision in record.genome.branch_path.decisions}),
    )


def _path_matches(decisions, target_path) -> bool:
    pairs = [(decision.layer_name, decision.selected) for decision in decisions]
    target_pairs = [tuple(item) for item in target_path]
    if not target_pairs:
        return False
    return pairs[: len(target_pairs)] == target_pairs or pairs[: max(len(target_pairs) - 1, 1)] == target_pairs[: max(len(target_pairs) - 1, 1)]


def _first_wrong(decisions, target_path):
    by_layer = {decision.layer_name: decision.selected for decision in decisions}
    for layer, expected in target_path:
        actual = by_layer.get(layer)
        if actual != expected:
            return layer, expected, actual
    return None, None, None

