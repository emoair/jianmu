from __future__ import annotations

from jianmu.self_learning.darwinforge.adaptive_layerwise_profile import LAYERWISE_LAYERS
from jianmu.self_learning.darwinforge.freeze_prune_transfer import run_freeze_prune_transfer
from jianmu.self_learning.darwinforge.layerwise_access_audit import write_layerwise_access_audit


def test_layerwise_access_audit_outputs_per_layer_metrics(tmp_path) -> None:
    freeze = run_freeze_prune_transfer(tmp_path, LAYERWISE_LAYERS)
    audit = write_layerwise_access_audit(tmp_path, freeze)
    assert audit["layerwise_access_audit_completed"] is True
    assert len(audit["layers"]) == len(LAYERWISE_LAYERS)
    assert {"touch_ratio", "freeze_ratio", "prune_ratio", "transfer_hit_rate"}.issubset(audit["layers"][0])
