from __future__ import annotations

import pytest

from jianmu.self_learning.darwinforge.billion_state_budget_profile import build_billion_state_profiles


def test_billion_state_profile_defines_upper_frontier_units() -> None:
    profiles = {row["profile_name"]: row for row in build_billion_state_profiles()}
    assert profiles["state_100M_reference"]["target_state_units"] == 100_000_000
    assert profiles["state_300M"]["target_state_units"] == 300_000_000
    assert profiles["state_600M"]["target_state_units"] == 600_000_000
    assert profiles["state_1B"]["target_state_units"] == 1_000_000_000


def test_billion_state_profile_caps_at_1b() -> None:
    with pytest.raises(ValueError):
        build_billion_state_profiles(["state_1_5B"])


def test_billion_state_materialization_level_explicit() -> None:
    profile = build_billion_state_profiles(["state_1B"])[0]
    assert profile["materialization_level"] in {"fully_materialized", "compressed_indexed", "lazy_indexed", "logical_budget_only", "simulated_budget"}
    assert profile["materialization_level"] != "fully_materialized"

