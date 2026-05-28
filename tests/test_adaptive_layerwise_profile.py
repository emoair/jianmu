from __future__ import annotations

from jianmu.self_learning.darwinforge.adaptive_layerwise_profile import build_adaptive_layerwise_profiles


def test_adaptive_layerwise_profile_defines_components() -> None:
    profiles = {row["profile_name"]: row for row in build_adaptive_layerwise_profiles()}
    combined = profiles["combined_hot_rebalanced_balanced_sampling_1B"]
    assert combined["allocation_profile"] == "hot_rebalanced_1B"
    assert combined["sampling_profile"] == "branch_activation_balanced"
    assert combined["profile_is_architecture_change"] is False
    layerwise = profiles["layerwise_sparse_1B_freeze_prune"]
    assert layerwise["layerwise_enabled"] is True
    assert layerwise["target_state_units_per_layer"] == 1_000_000_000
