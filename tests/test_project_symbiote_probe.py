from __future__ import annotations

from jianmu.self_learning.darwinforge.project_symbiote_probe import symbiote_metrics


def test_project_symbiote_probe_positive_shadow_metrics() -> None:
    metrics = symbiote_metrics()
    assert metrics["project_symbiote_positive"] is True
    assert metrics["comfort_zone_collapse_detected"] is False

