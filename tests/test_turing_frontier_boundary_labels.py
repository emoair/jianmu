from __future__ import annotations

from jianmu.self_learning.darwinforge.turing_frontier_boundary_labels import expected_action_for_category, is_supported_category


def test_frontier_boundary_labels() -> None:
    assert is_supported_category("bounded_control_hard_supported")
    assert expected_action_for_category("future_array_candidate") == "isolate_future"
    assert expected_action_for_category("unsupported_unbounded_loop") == "reject"

