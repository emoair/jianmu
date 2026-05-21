from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Iterable, List

from jianmu.self_learning.darwinforge.supported_boundary_spec import SupportedBoundarySpec, classify_against_supported_boundary


def classify_ood_boundary_samples(samples: List[Dict], spec: SupportedBoundarySpec | None = None, max_examples_per_class: int = 20) -> Dict:
    spec = spec or SupportedBoundarySpec()
    records = []
    for sample in samples:
        records.append(classify_ood_boundary_sample(sample, spec))
    summary = summarize_boundary_records(records, max_examples_per_class=max_examples_per_class)
    return {"records": records, **summary}


def classify_ood_boundary_sample(sample: Dict, spec: SupportedBoundarySpec | None = None) -> Dict:
    spec = spec or SupportedBoundarySpec()
    raw = sample.get("raw_text") or sample.get("input_text") or ""
    canonical = sample.get("canonical_text") or raw
    decision = classify_against_supported_boundary(
        sample,
        raw,
        canonical,
        {"ood_class": sample.get("ood_class"), "was_marked_ood": True, "unsupported_reason": sample.get("unsupported_reason")},
    )
    accepted = bool(sample.get("accepted_as_supported", True))
    label = _boundary_to_ood_label(decision.boundary_label, accepted, sample)
    recommended = _recommended_action(label, decision.recommended_action)
    return {
        "source_version": sample.get("source_branch") or sample.get("source_version") or "current",
        "sample_id": sample.get("sample_id"),
        "raw_text": raw or None,
        "canonical_text": canonical or None,
        "original_ood_class": sample.get("ood_class"),
        "original_false_accept_reason": sample.get("false_accept_reason"),
        "accepted_as_supported": accepted,
        "boundary_label": label,
        "boundary_decision": decision.boundary_label,
        "recommended_action": recommended,
        "reason": decision.reason,
        "confidence": decision.confidence,
    }


def summarize_boundary_records(records: Iterable[Dict], max_examples_per_class: int = 20) -> Dict:
    rows = list(records)
    counts = Counter(row["boundary_label"] for row in rows)
    examples = defaultdict(list)
    for row in rows:
        label = row["boundary_label"]
        if len(examples[label]) < max_examples_per_class:
            examples[label].append(row)
    return {
        "ood_boundary_distribution": dict(counts),
        "true_false_accept_count": counts.get("true_false_accept", 0),
        "near_ood_generalization_candidate_count": counts.get("near_ood_generalization_candidate", 0),
        "future_domain_candidate_count": counts.get("future_domain_candidate", 0),
        "label_too_strict_count": counts.get("label_too_strict", 0),
        "hard_ood_count": counts.get("hard_ood", 0),
        "unknown_count": counts.get("unknown", 0),
        "examples_by_boundary_label": dict(examples),
    }


def _boundary_to_ood_label(boundary_label: str, accepted: bool, sample: Dict) -> str:
    if boundary_label == "hard_reject":
        return "true_false_accept" if accepted else "hard_ood"
    if boundary_label == "future_domain_candidate":
        return "future_domain_candidate"
    if boundary_label == "near_supported_candidate":
        return "near_ood_generalization_candidate"
    if boundary_label == "label_review_needed":
        return "label_too_strict"
    if boundary_label == "supported":
        return "label_too_strict" if sample.get("split") == "ood" else "near_ood_generalization_candidate"
    return "unknown"


def _recommended_action(label: str, default: str) -> str:
    return {
        "true_false_accept": "reject_guard_needed",
        "hard_ood": "keep_rejected",
        "near_ood_generalization_candidate": "candidate_for_supported_expansion",
        "future_domain_candidate": "future_domain",
        "label_too_strict": "label_review_needed",
        "unknown": "unknown",
    }.get(label, default)
