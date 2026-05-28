from __future__ import annotations

from jianmu.self_learning.darwinforge.state_budget_profile import build_state_budget_profiles


def test_state_budget_profile_defines_units() -> None:
    profiles = {row["profile_name"]: row for row in build_state_budget_profiles()}
    assert profiles["state_10M"]["target_state_units"] == 10_000_000
    assert profiles["state_30M"]["target_state_units"] == 30_000_000
    assert profiles["state_100M"]["target_state_units"] == 100_000_000
    assert profiles["state_100M"]["candidate_fragment_bank_units"] > 0


def test_state_budget_materialization_level_is_explicit() -> None:
    profile = build_state_budget_profiles(["state_100M"])[0]
    assert profile["materialization_level"] in {"fully_materialized", "lazy_indexed", "compressed_indexed", "logical_budget_only", "simulated_budget"}
    assert profile["materialization_level"] != "fully_materialized"

