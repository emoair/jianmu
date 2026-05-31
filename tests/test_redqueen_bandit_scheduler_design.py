from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_bandit_scheduler_design import design_redqueen_bandit_scheduler, simulate_redqueen_bandit_scheduler


def test_bandit_scheduler_design_reward_terms() -> None:
    design = design_redqueen_bandit_scheduler()
    assert "boundary_risk_penalty" in design["penalty_terms"]
    assert design["readiness_for_implementation"] is True


def test_bandit_diagnostic_simulation_marks_diagnostic_only() -> None:
    sim = simulate_redqueen_bandit_scheduler({"top_positive_patterns": ["bounded_for_loop"]})
    assert sim["diagnostic_only"] is True
    assert sim["not_a_real_capability_result"] is True
