from __future__ import annotations

from collections import Counter
from typing import Dict, List

from jianmu.self_learning.darwinforge.supported_boundary_spec import SupportedBoundarySpec, classify_against_supported_boundary
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def replay_canonicalizer_reason(samples: List[Dict], boundary_spec: SupportedBoundarySpec | None = None) -> Dict:
    boundary_spec = boundary_spec or SupportedBoundarySpec()
    records = []
    for sample in samples:
        records.append(_replay_one(sample, boundary_spec))
    old_count = sum(1 for row in records if row["old_reason_was_canonicalizer_made_supported"])
    new_count = sum(1 for row in records if row["new_reason_is_canonicalizer_made_supported"])
    match_count = sum(1 for row in records if row["reason_match"] == "matched")
    detector_mismatch = sum(1 for row in records if row["reason_match"] == "detector_mismatch")
    missing_raw = sum(1 for row in records if row["reason_match"] == "missing_raw_text")
    counts = Counter(row["reason_match"] for row in records)
    reason = ""
    if old_count and not new_count:
        reason = "not_reproduced; old v0.8.1 guard-stress reason was present but current detector did not reproduce it"
    elif old_count and new_count:
        reason = "reproduced_for_some_samples"
    elif missing_raw:
        reason = "inconclusive; raw_text missing for some samples"
    else:
        reason = "no old canonicalizer reason in loaded slice"
    return {
        "records": records,
        "old_canonicalizer_reason_count": old_count,
        "new_canonicalizer_reason_count": new_count,
        "reason_match_count": match_count,
        "reason_not_match_count": len(records) - match_count,
        "reason_match_distribution": dict(counts),
        "reason_not_reproduced": reason,
        "detector_mismatch_count": detector_mismatch,
        "slice_mismatch_likely": bool(old_count and not new_count),
        "canonicalizer_reason_confirmed": bool(new_count and match_count),
        "boundary_spec_version": boundary_spec.version,
    }


def _replay_one(sample: Dict, boundary_spec: SupportedBoundarySpec) -> Dict:
    raw = sample.get("raw_text")
    old_canonical = sample.get("canonical_text")
    old_reason = sample.get("false_accept_reason")
    if not raw:
        return _missing_raw_record(sample, old_reason)
    canonical = canonicalize_symbols(raw)
    boundary = classify_against_supported_boundary(
        sample,
        raw,
        canonical.canonical_text,
        {"ood_class": sample.get("ood_class"), "was_marked_ood": True},
    ).to_dict()
    raw_signal = _contains_arithmetic_signal(raw)
    canonical_signal = _contains_arithmetic_signal(canonical.canonical_text)
    old_was = old_reason == "canonicalizer_made_it_look_supported"
    new_is = (
        not raw_signal
        and canonical_signal
        and bool(sample.get("accepted_as_supported"))
        and boundary["boundary_label"] != "supported"
        and canonical.changed
    )
    reason_match = _reason_match(old_was, new_is, old_reason)
    return {
        "sample_id": sample.get("sample_id"),
        "raw_text": raw,
        "old_canonical_text": old_canonical,
        "new_canonical_text": canonical.canonical_text,
        "old_false_accept_reason": old_reason,
        "new_false_accept_reason": "canonicalizer_made_it_look_supported" if new_is else _non_canonical_reason(sample, boundary),
        "old_reason_was_canonicalizer_made_supported": old_was,
        "new_reason_is_canonicalizer_made_supported": new_is,
        "canonical_changed": canonical.changed,
        "raw_arithmetic_signal": raw_signal,
        "canonical_arithmetic_signal": canonical_signal,
        "raw_task_intent_guess": _task_intent(raw),
        "canonical_task_intent_guess": _task_intent(canonical.canonical_text),
        "boundary_decision": boundary,
        "reason_match": reason_match,
    }


def _missing_raw_record(sample: Dict, old_reason: str | None) -> Dict:
    return {
        "sample_id": sample.get("sample_id"),
        "raw_text": None,
        "old_canonical_text": sample.get("canonical_text"),
        "new_canonical_text": None,
        "old_false_accept_reason": old_reason,
        "new_false_accept_reason": "unknown",
        "old_reason_was_canonicalizer_made_supported": old_reason == "canonicalizer_made_it_look_supported",
        "new_reason_is_canonicalizer_made_supported": False,
        "canonical_changed": None,
        "raw_arithmetic_signal": None,
        "canonical_arithmetic_signal": None,
        "raw_task_intent_guess": "missing",
        "canonical_task_intent_guess": "missing",
        "boundary_decision": {"boundary_label": "unknown", "recommended_action": "unknown", "reason": "missing raw_text", "confidence": 0.0},
        "reason_match": "missing_raw_text",
    }


def _reason_match(old_was: bool, new_is: bool, old_reason: str | None) -> str:
    if old_reason in (None, ""):
        return "missing_old_reason"
    if old_was and new_is:
        return "matched"
    if old_was and not new_is:
        return "detector_mismatch"
    if not old_was and new_is:
        return "not_matched"
    return "not_matched"


def _non_canonical_reason(sample: Dict, boundary: Dict) -> str:
    if boundary["boundary_label"] == "hard_reject":
        return "task_scope_too_broad"
    if boundary["boundary_label"] == "future_domain_candidate":
        return "arithmetic_family_too_loose"
    return sample.get("false_accept_reason") or "unknown"


def _contains_arithmetic_signal(text: str) -> bool:
    return any(ch.isdigit() for ch in text) and (any(op in text for op in ["+", "-", "*", "/"]) or any(cue in text for cue in ["加", "减", "乘", "除"]))


def _task_intent(text: str) -> str:
    lowered = text.lower()
    if any(cue in text for cue in ["算", "计算", "输出", "加", "减", "乘", "除"]) or any(cue in lowered for cue in ["calculate", "plus", "minus"]):
        return "arithmetic"
    return "unknown_or_non_arithmetic"
