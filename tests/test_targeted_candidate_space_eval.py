from __future__ import annotations

from jianmu.self_learning.darwinforge.targeted_candidate_space_eval import boundary_safety_metrics, evaluate_targeted_candidate_space
from jianmu.self_learning.darwinforge.targeted_candidate_space_profile import targeted_candidate_space_profile


def test_targeted_rerun_reports_candidate_miss_reduction() -> None:
    supported = [
        {"id": f"s{i}", "stage": "bounded_for_loop", "category": "bounded_control_hard_supported", "canonical_program": "bounded_for_loop:1"}
        for i in range(100)
    ]
    result = evaluate_targeted_candidate_space(supported, [], targeted_candidate_space_profile(), {"candidate_miss": 0.6024, "top1": 0.3776})
    assert result["candidate_miss_rate_targeted"] < 0.6024
    assert result["top1_targeted"] > 0.3776


def test_targeted_rerun_boundary_future_safety() -> None:
    boundary = [
        {"category": "future_function_candidate"},
        {"category": "future_array_candidate"},
        {"category": "future_recursion_candidate"},
        {"category": "unsupported_unbounded_loop"},
    ]
    result = boundary_safety_metrics(boundary)
    assert result["future_function_supported_accept_rate"] == 0.0
    assert result["future_array_supported_accept_rate"] == 0.0
    assert result["future_recursion_supported_accept_rate"] == 0.0
    assert result["unbounded_loop_false_accept_rate"] == 0.0

