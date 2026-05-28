from __future__ import annotations

SUPPORTED_CATEGORIES = {"current_supported_bounded_substrate", "bounded_control_hard_supported"}
FUTURE_CATEGORIES = {"future_function_candidate", "future_array_candidate", "future_recursion_candidate"}
UNSUPPORTED_CATEGORIES = {"unsupported_unbounded_loop", "near_ood_program", "true_false_accept_trap", "hard_ood", "label_review_candidate"}


def expected_action_for_category(category: str) -> str:
    if category in SUPPORTED_CATEGORIES:
        return "accept_supported"
    if category in FUTURE_CATEGORIES:
        return "isolate_future"
    if category == "near_ood_program":
        return "quarantine"
    if category == "label_review_candidate":
        return "review"
    return "reject"


def boundary_label_for_category(category: str) -> str:
    if category in SUPPORTED_CATEGORIES:
        return "current_supported"
    if category in FUTURE_CATEGORIES:
        return "future_domain"
    if category == "near_ood_program":
        return "near_ood"
    if category == "true_false_accept_trap":
        return "trap"
    if category == "hard_ood":
        return "hard_ood"
    if category == "label_review_candidate":
        return "review"
    return "unsupported"


def is_supported_category(category: str) -> bool:
    return category in SUPPORTED_CATEGORIES

