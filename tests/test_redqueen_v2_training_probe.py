from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_training_probe import run_redqueen_v2_probe


def test_redqueen_v2_training_probe_outputs_groups(tmp_path) -> None:
    result = run_redqueen_v2_probe("records/v0_9_19", tmp_path / "records", tmp_path / "dataset")
    assert len(result["metrics"]["runs"]) == 6
    assert result["readiness"]["best_experiment_group"] == "redqueen_v2_bandit_plus_contrastive_plus_hydrabudget"
