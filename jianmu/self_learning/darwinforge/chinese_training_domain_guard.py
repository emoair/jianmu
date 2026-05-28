from __future__ import annotations

from typing import Any, Dict


SUPPORTED_TRAIN_CATEGORIES = {
    "current_supported_bounded_substrate_zh",
    "bounded_control_hard_supported_zh",
}

FORBIDDEN_FEATURES = [
    "has_function",
    "has_array",
    "has_recursion",
    "has_unbounded_loop",
    "has_io",
    "has_system_call",
]


def can_enter_train_current(row: Dict[str, Any]) -> bool:
    features = row.get("language_features", {})
    return (
        row.get("support_status") == "current_supported"
        and row.get("input_language") == "zh"
        and row.get("category") in SUPPORTED_TRAIN_CATEGORIES
        and row.get("target_ir") is not None
        and row.get("expected_output") is not None
        and not any(features.get(name, False) for name in FORBIDDEN_FEATURES)
    )


def classify_training_domain(row: Dict[str, Any]) -> str:
    if can_enter_train_current(row):
        return "train_current_allowed"
    if row.get("support_status") == "current_supported" and row.get("input_language") != "zh":
        return "blocked_non_chinese_current_supported"
    if row.get("support_status") in {"future_domain", "near_supported"}:
        return "isolated_future_or_near_supported"
    if row.get("support_status") in {"unsupported", "trap", "hard_ood", "review"}:
        return "boundary_or_review"
    return "blocked_unknown"

