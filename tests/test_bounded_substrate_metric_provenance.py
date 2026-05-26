from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_metric_provenance import KEY_METRICS


def test_bounded_substrate_metric_provenance_has_required_metrics() -> None:
    assert "supported_candidate_hit_before" in KEY_METRICS
    assert "top1_supported_correct_after" in KEY_METRICS
