from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List


OOD_PRECISION_LABELS = {
    "hard_ood",
    "near_ood_generalization_candidate",
    "future_domain_candidate",
    "label_too_strict",
    "true_false_accept",
    "unknown",
}


@dataclass(frozen=True)
class OODPrecisionRecord:
    sample_id: str
    raw_text: str
    canonical_text: str
    ood_class: str
    accepted_as_supported: bool
    generated_targetir: bool
    targetir_exact_match_if_available: bool | None
    output_match_if_available: bool | None
    rejection_layer: str
    false_accept_reason: str
    precision_label: str
    reason: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def label_ood_precision(sample: Dict, guard_record: Dict) -> OODPrecisionRecord:
    raw = sample.get("input_text", guard_record.get("raw_text", ""))
    canonical = guard_record.get("canonical_text", raw)
    accepted = bool(guard_record.get("accepted_as_supported", False))
    klass = guard_record.get("ood_class", sample.get("input_mode", "unknown"))
    reason = guard_record.get("false_accept_reason", "unknown")
    label, explanation = _precision_label(raw, canonical, klass, reason, accepted, sample)
    return OODPrecisionRecord(
        sample_id=sample.get("sample_id", guard_record.get("sample_id", "")),
        raw_text=raw,
        canonical_text=canonical,
        ood_class=klass,
        accepted_as_supported=accepted,
        generated_targetir=bool(guard_record.get("generated_targetir", False)),
        targetir_exact_match_if_available=guard_record.get("targetir_exact_match_if_available"),
        output_match_if_available=guard_record.get("output_match_if_available"),
        rejection_layer=guard_record.get("rejection_layer", "unknown"),
        false_accept_reason=reason,
        precision_label=label,
        reason=explanation,
    )


def run_ood_precision_audit(samples: List[Dict], guard_records: List[Dict]) -> Dict:
    sample_by_id = {sample.get("sample_id"): sample for sample in samples}
    records = []
    for guard in guard_records:
        sample = sample_by_id.get(guard.get("sample_id"), guard)
        records.append(label_ood_precision(sample, guard).to_dict())
    summary = summarize_ood_precision(records)
    return {"records": records, **summary}


def summarize_ood_precision(records: Iterable[Dict]) -> Dict:
    rows = list(records)
    counts = Counter(row.get("precision_label", "unknown") for row in rows)
    return {
        "ood_precision_distribution": dict(counts),
        "true_false_accept_count": counts.get("true_false_accept", 0),
        "near_ood_generalization_candidate_count": counts.get("near_ood_generalization_candidate", 0),
        "future_domain_candidate_count": counts.get("future_domain_candidate", 0),
        "label_too_strict_count": counts.get("label_too_strict", 0),
        "hard_ood_count": counts.get("hard_ood", 0),
        "unknown_count": counts.get("unknown", 0),
    }


def _precision_label(raw: str, canonical: str, klass: str, reason: str, accepted: bool, sample: Dict) -> tuple[str, str]:
    text = raw.lower()
    if not accepted:
        return "hard_ood" if klass in {"ood_english_sentence", "ood_unrelated_request"} else "unknown", "not accepted; kept as rejection-side audit"
    if klass in {"ood_english_sentence", "ood_unrelated_request", "instruction_not_programming"}:
        return "true_false_accept", "clearly outside current arithmetic/programming scope"
    if klass in {"division_by_zero", "non_exact_division", "unsupported_operator", "unsupported_depth"}:
        return "future_domain_candidate", "unsupported now but plausible future arithmetic/domain extension"
    if reason == "canonicalizer_made_it_look_supported" and _has_arithmetic_intent(text):
        return "near_ood_generalization_candidate", "surface form differs but arithmetic intent is nearby"
    if sample.get("unsupported_reason") in {"label_too_strict"}:
        return "label_too_strict", "metadata marks label review needed"
    if klass == "unsupported_arithmetic":
        return "future_domain_candidate", "unsupported arithmetic accepted; future support candidate"
    return "unknown", "insufficient information for precise OOD label"


def _has_arithmetic_intent(text: str) -> bool:
    cues = ["算", "计算", "输出", "加", "减", "乘", "除", "+", "-", "*", "/", "plus", "minus"]
    return any(cue in text for cue in cues)

