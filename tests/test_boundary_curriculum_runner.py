from jianmu.self_learning.darwinforge.boundary_curriculum_runner import run_boundary_curriculum_runner
from jianmu.self_learning.datasets.boundary_aware_generator import generate_boundary_aware_samples


def test_boundary_curriculum_runner_runs_all_stages():
    rows = generate_boundary_aware_samples(600, seed=1)
    result = run_boundary_curriculum_runner(rows, rows, mode="quick", worker_count=4)
    assert len(result["stage_metrics"]) == 6
    assert result["real_promotion_enabled"] is False


def test_boundary_curriculum_runner_does_not_use_labels_as_features():
    rows = generate_boundary_aware_samples(600, seed=2)
    result = run_boundary_curriculum_runner(rows, rows, mode="quick", worker_count=4)
    assert result["labels_used_as_inference_features"] is False
