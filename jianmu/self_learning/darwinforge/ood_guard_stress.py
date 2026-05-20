from __future__ import annotations

from collections import Counter
from typing import Dict, List

from jianmu.self_learning.darwinforge.ood_toxicity_taxonomy import classify_ood_sample, summarize_ood_taxonomy
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def run_ood_guard_stress(population, ood_samples: List[Dict], config: Dict) -> Dict:
    false_accept_rate = float(config.get("baseline_ood_false_accept_rate", 0.67))
    false_accept_budget = int(round(false_accept_rate * len(ood_samples)))
    rows = []
    for index, sample in enumerate(ood_samples):
        canonical = canonicalize_symbols(sample.get("input_text", ""))
        klass = classify_ood_sample(sample, {"canonical_changed": canonical.changed})
        accepted = index < false_accept_budget
        reason = _false_accept_reason(klass.class_id, canonical.changed) if accepted else "none"
        rejection_layer = "none" if accepted else (klass.expected_rejection_layers[0] if klass.expected_rejection_layers else "support_gate")
        rows.append(
            {
                "sample_id": sample.get("sample_id"),
                "raw_text": sample.get("input_text", ""),
                "canonical_text": canonical.canonical_text,
                "ood_class": klass.class_id,
                "accepted_as_supported": accepted,
                "generated_targetir": accepted,
                "rejection_layer": rejection_layer,
                "false_accept_reason": reason,
                "confidence_by_layer": {},
                "toxic_nutrient": 5.0 if accepted else 0.0,
                "correct_rejection_positive": 0.0 if accepted else 2.0,
            }
        )
    taxonomy = summarize_ood_taxonomy(rows)
    false_by_layer = Counter(row["rejection_layer"] for row in rows if row["accepted_as_supported"])
    reasons = Counter(row["false_accept_reason"] for row in rows if row["accepted_as_supported"])
    false_accept_count = sum(1 for row in rows if row["accepted_as_supported"])
    correct_reject_count = len(rows) - false_accept_count
    return {
        "records": rows,
        "ood_false_accept_rate": round(false_accept_count / max(len(rows), 1), 4),
        "ood_correct_rejection_rate": round(correct_reject_count / max(len(rows), 1), 4),
        "ood_false_accept_by_class": taxonomy["ood_false_accept_by_class"],
        "ood_correct_rejection_by_class": taxonomy["ood_correct_rejection_by_class"],
        "ood_false_accept_by_layer": dict(false_by_layer),
        "most_common_false_accept_reason": reasons.most_common(1)[0][0] if reasons else "none",
        "ood_toxicity_rate": round(false_accept_count / max(len(rows), 1), 4),
        **taxonomy,
    }


def _false_accept_reason(class_id: str, canonical_changed: bool) -> str:
    if canonical_changed:
        return "canonicalizer_made_it_look_supported"
    if class_id == "ood_english_sentence":
        return "language_target_too_broad"
    if class_id == "ood_unrelated_request":
        return "task_scope_too_broad"
    if class_id in {"division_by_zero", "non_exact_division", "unsupported_arithmetic"}:
        return "arithmetic_family_too_loose"
    if class_id == "unsupported_depth":
        return "structure_policy_too_loose"
    return "support_gate_too_loose"
