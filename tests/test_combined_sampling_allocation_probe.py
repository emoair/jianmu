from __future__ import annotations

from jianmu.self_learning.darwinforge.combined_sampling_allocation_probe import write_sampling_profiles


def test_combined_sampling_allocation_profile(tmp_path) -> None:
    result = write_sampling_profiles(tmp_path)
    rows = {row["sampling_profile"]: row for row in result["profiles"]}
    combined = rows["combined_branch_activation_plus_supported_control"]
    assert combined["future_domains_remain_out_of_train_current"] is True
    assert combined["supported_control_exposure"] > rows["original_sampling_reference"]["supported_control_exposure"]
