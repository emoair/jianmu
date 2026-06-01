from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_bandit_scheduler import build_bandit_policy


def test_redqueen_v2_bandit_scheduler_arm_selection() -> None:
    policy = build_bandit_policy({"patterns": [], "top_positive_patterns": ["bounded_for_loop"], "low_roi_patterns": []})
    assert policy["scheduler"] == "epsilon_greedy_scheduler"
    assert "bounded_for_loop" in policy["promoted_arms"]
