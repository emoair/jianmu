from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List

from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def audit_canonicalization_ood_sample(sample: Dict) -> Dict:
    raw = sample.get("input_text", "")
    canonical = canonicalize_symbols(raw)
    raw_signal = _contains_arithmetic_signal(raw)
    canonical_signal = _contains_arithmetic_signal(canonical.canonical_text)
    made_supported = (not raw_signal) and canonical_signal and canonical.changed
    beneficial = made_supported and _looks_like_arithmetic_request(raw)
    dangerous = made_supported and not beneficial
    action = _suggested_action(made_supported, beneficial, dangerous, sample)
    return {
        "sample_id": sample.get("sample_id"),
        "raw_text": raw,
        "canonical_text": canonical.canonical_text,
        "canonical_changed": canonical.changed,
        "raw_contains_arithmetic_signal": raw_signal,
        "canonical_contains_arithmetic_signal": canonical_signal,
        "raw_task_intent_guess": "arithmetic" if _looks_like_arithmetic_request(raw) else "unknown_or_non_arithmetic",
        "canonical_task_intent_guess": "arithmetic" if canonical_signal else "unknown_or_non_arithmetic",
        "made_supported_by_canonicalization": made_supported,
        "likely_beneficial_generalization": beneficial,
        "likely_dangerous_false_accept": dangerous,
        "suggested_action": action,
    }


def run_canonicalization_ood_audit(samples: List[Dict]) -> Dict:
    records = [audit_canonicalization_ood_sample(sample) for sample in samples]
    return {"records": records, **summarize_canonicalization_ood(records)}


def summarize_canonicalization_ood(records: Iterable[Dict]) -> Dict:
    rows = list(records)
    action_counts = Counter(row["suggested_action"] for row in rows)
    return {
        "canonicalizer_made_supported_count": sum(1 for row in rows if row["made_supported_by_canonicalization"]),
        "beneficial_generalization_candidate_count": sum(1 for row in rows if row["likely_beneficial_generalization"]),
        "dangerous_false_accept_count": sum(1 for row in rows if row["likely_dangerous_false_accept"]),
        "label_review_candidate_count": action_counts.get("label_review_needed", 0),
        "suggested_action_distribution": dict(action_counts),
    }


def _contains_arithmetic_signal(text: str) -> bool:
    return any(token in text for token in ["+", "-", "*", "/", "加", "减", "乘", "除"]) or any(ch.isdigit() for ch in text)


def _looks_like_arithmetic_request(text: str) -> bool:
    lowered = text.lower()
    return any(cue in text for cue in ["算", "计算", "输出", "加", "减", "乘", "除"]) or any(cue in lowered for cue in ["calculate", "plus", "minus"])


def _suggested_action(made_supported: bool, beneficial: bool, dangerous: bool, sample: Dict) -> str:
    if sample.get("unsupported_reason") == "label_too_strict":
        return "label_review_needed"
    if beneficial:
        return "keep_as_generalization_candidate"
    if dangerous:
        return "reject_guard_needed"
    if sample.get("input_mode") == "unsupported_arithmetic":
        return "future_supported_slice"
    return "unknown"

