from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_robustness_eval import run_robustness_eval


def test_mirrorforge_robustness_eval(tmp_path):
    result = run_robustness_eval(tmp_path)
    assert result["robustness"]["perturbation_robustness_completed"] is True
    assert result["robustness"]["robustness_score"] > 0.9
    assert result["abstraction_metrics"]["training_eval_completed"] is True
