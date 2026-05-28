from __future__ import annotations

from jianmu.self_learning.darwinforge.adaptive_layerwise_failure_analysis import write_adaptive_layerwise_failure_analysis
from jianmu.self_learning.darwinforge.adaptive_layerwise_profile import LAYERWISE_LAYERS
from jianmu.self_learning.darwinforge.freeze_prune_transfer import run_freeze_prune_transfer
from jianmu.self_learning.darwinforge.layerwise_access_audit import write_layerwise_access_audit


def test_adaptive_layerwise_failure_analysis_outputs_examples(tmp_path) -> None:
    freeze = run_freeze_prune_transfer(tmp_path, LAYERWISE_LAYERS)
    audit = write_layerwise_access_audit(tmp_path, freeze)
    result = write_adaptive_layerwise_failure_analysis(tmp_path, audit)
    assert result["failure_analysis_completed"] is True
    assert (tmp_path / "adaptive_layerwise_failure_examples.jsonl").exists()
