from __future__ import annotations

from jianmu.self_learning.darwinforge.targeted_candidate_space_profile import targeted_candidate_space_profile


def test_targeted_candidate_space_profile_records_best_budget() -> None:
    profile = targeted_candidate_space_profile()
    assert profile["beam_size"] == 64
    assert profile["candidate_budget"] == 512
    assert profile["control_template_budget"] == "xlarge"
    assert profile["root_expansion_budget"] == "8x"
    assert profile["memory_budget"] == "8x"


def test_targeted_profile_not_architecture_change() -> None:
    profile = targeted_candidate_space_profile()
    assert profile["profile_is_architecture_change"] is False
    assert profile["profile_not_claimed_as_default_architecture"] is True

