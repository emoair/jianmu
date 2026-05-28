from __future__ import annotations

from jianmu.self_learning.darwinforge.adaptive_layerwise_allocator import run_adaptive_layerwise_memory_guard
from jianmu.self_learning.darwinforge.adaptive_layerwise_profile import build_adaptive_layerwise_profiles


def test_layerwise_1b_is_lazy_indexed_not_fully_materialized(tmp_path) -> None:
    profile = build_adaptive_layerwise_profiles(["layerwise_sparse_1B_freeze_prune"])[0]
    guard = run_adaptive_layerwise_memory_guard(tmp_path, [profile])
    row = guard["profiles"][0]
    assert row["materialization_level"] == "lazy_indexed"
    assert all(layer["can_fully_materialize"] is False for layer in row["layers"])
    assert all(layer["recommended_materialization_level"] == "lazy_indexed" for layer in row["layers"])
