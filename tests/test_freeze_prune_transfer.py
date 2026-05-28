from __future__ import annotations

from jianmu.self_learning.darwinforge.adaptive_layerwise_profile import LAYERWISE_LAYERS
from jianmu.self_learning.darwinforge.freeze_prune_transfer import run_freeze_prune_transfer


def test_freeze_prune_records_frozen_and_pruned_units(tmp_path) -> None:
    result = run_freeze_prune_transfer(tmp_path, LAYERWISE_LAYERS)
    assert result["frozen_state_units"] > 0
    assert result["pruned_state_units"] > 0
    assert (tmp_path / "freeze_prune_trace.jsonl").exists()


def test_freeze_prune_does_not_modify_architecture(tmp_path) -> None:
    result = run_freeze_prune_transfer(tmp_path, LAYERWISE_LAYERS)
    assert all(row["freeze_prune_is_architecture_change"] is False for row in result["layers"])
