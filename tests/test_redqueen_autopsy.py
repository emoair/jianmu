from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs, run_redqueen_autopsy


def test_redqueen_autopsy_loads_v0_9_17_records() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    assert data["readiness"]["best_experiment_group"] == "redqueen_plus_hydrabudget"
    assert data["failure_mining"]["data_need_specs"]


def test_redqueen_autopsy_end_to_end(tmp_path: Path) -> None:
    result = run_redqueen_autopsy("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum", tmp_path)
    assert result["redqueen_autopsy_readiness"]["redqueen_autopsy_completed"] is True
    assert (tmp_path / "redqueen_spec_attribution.json").exists()
