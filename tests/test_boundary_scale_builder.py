from pathlib import Path

from jianmu.self_learning.datasets.boundary_scale_builder import build_boundary_scale


def test_scale_builder_generates_medium_dataset(tmp_path):
    summary = build_boundary_scale("small", tmp_path, seed=1)
    assert Path(summary["manifest_path"]).exists()
    assert summary["actual_total"] == 6000
    assert summary["audit"]["audit_passed"]


def test_scale_builder_records_actual_total_if_short(tmp_path):
    summary = build_boundary_scale("small", tmp_path, seed=2)
    assert "actual_total" in summary
    assert "reason_if_short" in summary
