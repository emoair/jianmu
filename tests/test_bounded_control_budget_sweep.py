from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_control_budget_sweep import run_budget_sweep


def test_budget_sweep_runs_phased_not_cartesian(tmp_path) -> None:
    result = run_budget_sweep(tmp_path, [8, 16], [32, 64], ["small", "medium"], ["1x", "2x"], ["baseline", "2x"])
    assert result["phased_not_cartesian"] is True
    assert len(result["configs"]) == 10


def test_budget_sweep_does_not_change_architecture(tmp_path) -> None:
    result = run_budget_sweep(tmp_path, [8], [32], ["small"], ["1x"], ["baseline"])
    assert result["diagnostic_only_not_training_gain"] is True

