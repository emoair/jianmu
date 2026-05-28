from __future__ import annotations

from jianmu.self_learning.darwinforge.access_aware_reallocation_probe import run_access_aware_reallocation_probe


def test_access_aware_reallocation_probe_not_architecture_change(tmp_path) -> None:
    result = run_access_aware_reallocation_probe("records/v0_9_12", tmp_path)
    assert result["access_aware_reallocation_probe_completed"] is True
    assert result["best_reallocation_profile"] == "hot_rebalanced_1B"
    assert all(row["reallocation_profile_is_architecture_change"] is False for row in result["profiles"])


def test_reallocation_profiles_report_layer_budgets(tmp_path) -> None:
    result = run_access_aware_reallocation_probe("records/v0_9_12", tmp_path)
    row = result["profiles"][0]
    assert row["allocated_units_by_layer"]["candidate_fragment_leaf"] > 0
    assert row["touched_units_by_layer"]["candidate_fragment_leaf"] > 0
