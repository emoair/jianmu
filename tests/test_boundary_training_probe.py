from jianmu.self_learning.darwinforge.boundary_training_probe import run_boundary_training_probe
from jianmu.self_learning.datasets.boundary_scale_builder import build_boundary_scale


def test_boundary_probe_loads_dataset_and_runs(tmp_path):
    summary = build_boundary_scale("small", tmp_path, seed=11)
    result = run_boundary_training_probe(summary["output_dir"], mode="quick", worker_count=4)
    assert result["dataset_load_success"]
    assert result["train_sample_count"] > 0
    assert result["eval_sample_count"] > 0


def test_boundary_probe_reports_emergent_diagnostics(tmp_path):
    summary = build_boundary_scale("small", tmp_path, seed=12)
    result = run_boundary_training_probe(summary["output_dir"], mode="quick", worker_count=4)
    assert "emergent_rejection_signal_confirmed" in result["emergent_rejection_diagnostics"]
