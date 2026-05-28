from __future__ import annotations

from jianmu.self_learning.darwinforge.adaptive_layerwise_allocator import allocate_adaptive_profile, run_adaptive_layerwise_memory_guard
from jianmu.self_learning.darwinforge.adaptive_layerwise_eval import build_adaptive_comparison, evaluate_adaptive_layerwise_profiles
from jianmu.self_learning.darwinforge.adaptive_layerwise_profile import build_adaptive_layerwise_profiles
from jianmu.self_learning.darwinforge.freeze_prune_transfer import run_freeze_prune_transfer


def test_adaptive_layerwise_eval_compares_profiles(tmp_path) -> None:
    profiles = build_adaptive_layerwise_profiles()
    guard = run_adaptive_layerwise_memory_guard(tmp_path, profiles)
    allocations = {profile["profile_name"]: allocate_adaptive_profile(profile, guard) for profile in profiles}
    freeze = run_freeze_prune_transfer(tmp_path, profiles[-1]["layers"])
    metrics = evaluate_adaptive_layerwise_profiles(tmp_path, profiles, allocations, freeze)
    comparison = build_adaptive_comparison(tmp_path, metrics, freeze)
    assert comparison["combined_profile_improves_over_each_component"] is True
    assert comparison["layerwise_profile_improves_over_combined"] is True
    assert comparison["profile_promotion_completed"] is False
