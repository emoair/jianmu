from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.darwinforge.candidate import CandidateRecord


@dataclass
class CandidateRankRecord:
    sample_id: str
    group_id: str
    candidate_id: str
    original_rank: int
    original_score: float
    target_ir_pred: Optional[str]
    target_ir_true: Optional[str]
    exact_match: bool
    expected_output_match: bool
    rejected: bool
    rerank_score: float
    rerank_rank: int
    quadrant: str

    def to_dict(self) -> Dict:
        return {
            "sample_id": self.sample_id,
            "group_id": self.group_id,
            "candidate_id": self.candidate_id,
            "original_rank": self.original_rank,
            "original_score": self.original_score,
            "target_ir_pred": self.target_ir_pred,
            "target_ir_true": self.target_ir_true,
            "exact_match": self.exact_match,
            "expected_output_match": self.expected_output_match,
            "rejected": self.rejected,
            "rerank_score": self.rerank_score,
            "rerank_rank": self.rerank_rank,
            "quadrant": self.quadrant,
        }


@dataclass
class GroupBeamResult:
    group_id: str
    selected_candidate_ids: List[str]
    group_score: float
    group_targetir_consistency: bool
    group_targetir_exact_match: bool
    cross_mode_consistency: bool
    collapse_detected: bool
    low_score_correct_count: int
    high_score_wrong_count: int

    def to_dict(self) -> Dict:
        return {
            "group_id": self.group_id,
            "selected_candidate_ids": list(self.selected_candidate_ids),
            "group_score": self.group_score,
            "group_targetir_consistency": self.group_targetir_consistency,
            "group_targetir_exact_match": self.group_targetir_exact_match,
            "cross_mode_consistency": self.cross_mode_consistency,
            "collapse_detected": self.collapse_detected,
            "low_score_correct_count": self.low_score_correct_count,
            "high_score_wrong_count": self.high_score_wrong_count,
        }


@dataclass
class PruningCandidate:
    branch_signature: str
    reason: str
    observed_count: int = 0
    high_score_wrong_count: int = 0
    examples: List[str] = field(default_factory=list)
    suggested_action: str = "downrank"

    def to_dict(self) -> Dict:
        return {
            "branch_signature": self.branch_signature,
            "reason": self.reason,
            "observed_count": self.observed_count,
            "high_score_wrong_count": self.high_score_wrong_count,
            "examples": list(self.examples[:5]),
            "suggested_action": self.suggested_action,
        }


def classify_candidate_quadrant(candidate: CandidateRecord, task: Dict, original_rank: int, original_score: float, high_score_cutoff: int = 0) -> str:
    exact = bool(task.get("supported") and candidate.phenotype.target_ir_canonical == task.get("target_ir_canonical") and not candidate.phenotype.unsupported_pred)
    high_score = original_rank <= high_score_cutoff
    if exact and high_score:
        return "high_score_correct"
    if (not exact) and high_score:
        return "high_score_wrong"
    if exact and not high_score:
        return "low_score_correct"
    return "low_score_wrong"


def rerank_candidates_for_sample(candidate_records: List[CandidateRecord], task: Dict) -> List[CandidateRankRecord]:
    original = sorted(candidate_records, key=lambda record: record.fitness_report.total_fitness, reverse=True)
    ranked = []
    for original_rank, record in enumerate(original):
        original_score = float(record.fitness_report.total_fitness)
        supported = bool(task.get("supported"))
        exact = bool(supported and record.phenotype.target_ir_canonical == task.get("target_ir_canonical") and not record.phenotype.unsupported_pred)
        expected = bool(supported and record.phenotype.expected_output_pred == task.get("expected_output") and not record.phenotype.unsupported_pred)
        false_accept_unsupported = bool((not supported) and not record.phenotype.unsupported_pred)
        false_reject_supported = bool(supported and record.phenotype.unsupported_pred)
        correct_unsupported = bool((not supported) and record.phenotype.unsupported_pred)
        wrong_target = bool(supported and record.phenotype.target_ir_canonical and not exact)
        rerank_score = original_score
        rerank_score += 5.0 if exact else 0.0
        rerank_score += 3.0 if expected else 0.0
        rerank_score += 2.0 if correct_unsupported else 0.0
        rerank_score -= 5.0 if false_accept_unsupported else 0.0
        rerank_score -= 3.0 if wrong_target else 0.0
        rerank_score -= 2.0 if false_reject_supported else 0.0
        ranked.append(
            CandidateRankRecord(
                sample_id=task["sample_id"],
                group_id=task["paraphrase_group"],
                candidate_id=record.genome.genome_id,
                original_rank=original_rank,
                original_score=round(original_score, 4),
                target_ir_pred=record.phenotype.target_ir_canonical,
                target_ir_true=task.get("target_ir_canonical"),
                exact_match=exact,
                expected_output_match=expected,
                rejected=record.phenotype.unsupported_pred,
                rerank_score=round(rerank_score, 4),
                rerank_rank=-1,
                quadrant=classify_candidate_quadrant(record, task, original_rank, original_score),
            )
        )
    ranked.sort(key=lambda item: (item.rerank_score, -item.original_rank), reverse=True)
    for rerank_rank, item in enumerate(ranked):
        item.rerank_rank = rerank_rank
    return ranked


def select_group_beam(candidate_records_by_sample: List[List[CandidateRecord]], group_samples: List[Dict], beam_width: int = 5) -> GroupBeamResult:
    ranked_by_sample = [rerank_candidates_for_sample(records, sample)[:beam_width] for records, sample in zip(candidate_records_by_sample, group_samples)]
    records_by_id = {record.genome.genome_id: record for records in candidate_records_by_sample for record in records}
    hypotheses = set()
    for ranked in ranked_by_sample:
        for item in ranked:
            if item.target_ir_pred:
                hypotheses.add(item.target_ir_pred)
    if not any(sample.get("supported") for sample in group_samples):
        hypotheses.add("<all_rejected>")
    if not hypotheses:
        hypotheses.add("<all_rejected>")
    best = None
    for hypothesis in hypotheses:
        selected = []
        for ranked in ranked_by_sample:
            if hypothesis == "<all_rejected>":
                preferred = [item for item in ranked if item.rejected]
            else:
                preferred = [item for item in ranked if item.target_ir_pred == hypothesis and not item.rejected]
            selected.append((preferred or ranked)[0])
        result = _score_group_hypothesis(hypothesis, selected, group_samples, records_by_id)
        if best is None or result.group_score > best.group_score:
            best = result
    return best


def collect_pruning_candidates(rank_records: List[CandidateRankRecord], candidate_records: List[CandidateRecord]) -> List[PruningCandidate]:
    by_id = {record.genome.genome_id: record for record in candidate_records}
    buckets: Dict[str, PruningCandidate] = {}
    for rank in rank_records:
        if rank.quadrant != "high_score_wrong":
            continue
        record = by_id.get(rank.candidate_id)
        if not record:
            continue
        signature = branch_signature(record)
        item = buckets.setdefault(
            signature,
            PruningCandidate(
                branch_signature=signature,
                reason="high_score_wrong_shortcut",
                suggested_action="downrank",
            ),
        )
        item.observed_count += 1
        item.high_score_wrong_count += 1
        item.examples.append(rank.sample_id)
    return sorted(buckets.values(), key=lambda item: (item.high_score_wrong_count, item.branch_signature), reverse=True)


def branch_signature(record: CandidateRecord) -> str:
    if not record.genome.branch_path.decisions:
        return "<empty_path>"
    return "|".join(f"{decision.layer_name}={decision.selected}" for decision in record.genome.branch_path.decisions)


def _score_group_hypothesis(hypothesis: str, selected: List[CandidateRankRecord], group_samples: List[Dict], records_by_id: Dict[str, CandidateRecord]) -> GroupBeamResult:
    supported = all(sample.get("supported") for sample in group_samples)
    target = group_samples[0].get("target_ir_canonical")
    selected_records = [records_by_id[item.candidate_id] for item in selected]
    accepted_targetirs = [record.phenotype.target_ir_canonical for record in selected_records if not record.phenotype.unsupported_pred and record.phenotype.target_ir_canonical]
    all_rejected = all(record.phenotype.unsupported_pred for record in selected_records)
    consistency = bool(accepted_targetirs) and len(set(accepted_targetirs)) == 1
    exact = bool(supported) and all((not record.phenotype.unsupported_pred) and record.phenotype.target_ir_canonical == target for record in selected_records)
    expected_matches = sum(1 for record, sample in zip(selected_records, group_samples) if record.phenotype.expected_output_pred == sample.get("expected_output") and sample.get("supported"))
    by_mode = defaultdict(set)
    for record, sample in zip(selected_records, group_samples):
        if record.phenotype.target_ir_canonical and not record.phenotype.unsupported_pred:
            by_mode[sample.get("input_mode")].add(record.phenotype.target_ir_canonical)
    cross_mode = bool(by_mode) and len(by_mode) >= 2 and len(set().union(*by_mode.values())) == 1
    wrong_consistent = supported and consistency and accepted_targetirs[0] != target
    ood_correct = (not supported) and all_rejected
    ood_false_accept = (not supported) and not all_rejected
    supported_all_rejected = supported and all_rejected
    score = sum(item.rerank_score for item in selected)
    score += 4.0 if exact else 0.0
    score += 2.0 if consistency else 0.0
    score += 1.0 if cross_mode else 0.0
    score += expected_matches
    score += 1.0 if ood_correct else 0.0
    score -= 4.0 if wrong_consistent else 0.0
    score -= 3.0 if ood_false_accept else 0.0
    score -= 2.0 if supported_all_rejected else 0.0
    score -= 1.0 if supported and not consistency else 0.0
    return GroupBeamResult(
        group_id=group_samples[0]["paraphrase_group"],
        selected_candidate_ids=[item.candidate_id for item in selected],
        group_score=round(score, 4),
        group_targetir_consistency=bool(consistency),
        group_targetir_exact_match=bool(exact),
        cross_mode_consistency=bool(cross_mode),
        collapse_detected=bool(wrong_consistent),
        low_score_correct_count=sum(1 for item in selected if item.quadrant == "low_score_correct"),
        high_score_wrong_count=sum(1 for item in selected if item.quadrant == "high_score_wrong"),
    )
