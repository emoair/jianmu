from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_bandit_stability import analyze_bandit_stability


def test_bandit_stability_analysis() -> None:
    policy = {"promoted_arms": ["a", "contrast_b"], "retired_arms": [], "epsilon_min": 0.05, "arm_selection_history": [{"selected_arm": "a"}, {"selected_arm": "contrast_b"}, {"selected_arm": "a"}, {"selected_arm": "contrast_b"}], "reward_trace": [{"reward": 0.2}, {"reward": 0.25}]}
    result = analyze_bandit_stability(policy)
    assert result["scheduler_stable"]
    assert result["contrastive_arm_selection_rate"] > 0
