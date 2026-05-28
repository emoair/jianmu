from __future__ import annotations

from typing import Dict


CATEGORY_PLAN: Dict[str, Dict[str, object]] = {
    "current_supported_bounded_substrate": {"ratio": 0.20, "support_status": "current_supported", "stage": "bounded_control_supported"},
    "bounded_control_hard_supported": {"ratio": 0.20, "support_status": "current_supported", "stage": "bounded_control_hard_supported"},
    "near_supported_pure_function": {"ratio": 0.10, "support_status": "future_domain", "stage": "pure_function_frontier"},
    "near_supported_fixed_array": {"ratio": 0.10, "support_status": "future_domain", "stage": "fixed_array_frontier"},
    "future_function_call_graph": {"ratio": 0.08, "support_status": "future_domain", "stage": "function_call_graph_frontier"},
    "future_array_loop_combination": {"ratio": 0.08, "support_status": "future_domain", "stage": "array_loop_frontier"},
    "future_bounded_recursion_candidate": {"ratio": 0.06, "support_status": "future_domain", "stage": "bounded_recursion_frontier"},
    "unsupported_unbounded_recursion": {"ratio": 0.04, "support_status": "unsupported", "stage": "unbounded_recursion"},
    "unsupported_unbounded_loop": {"ratio": 0.04, "support_status": "unsupported", "stage": "unbounded_loop"},
    "scope_lifetime_edge_cases": {"ratio": 0.03, "support_status": "review", "stage": "scope_lifetime_edge"},
    "trap_unsafe_io_system": {"ratio": 0.03, "support_status": "trap", "stage": "unsafe_io_system"},
    "adversarial_natural_language_trap": {"ratio": 0.02, "support_status": "trap", "stage": "adversarial_nl"},
    "hard_ood": {"ratio": 0.01, "support_status": "unsupported", "stage": "hard_ood"},
    "label_review_candidate": {"ratio": 0.01, "support_status": "review", "stage": "label_review"},
}


def support_status_for_category(category: str) -> str:
    return str(CATEGORY_PLAN[category]["support_status"])


def stage_for_category(category: str) -> str:
    return str(CATEGORY_PLAN[category]["stage"])


def is_current_supported(category: str) -> bool:
    return support_status_for_category(category) == "current_supported"
