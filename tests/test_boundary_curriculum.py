from jianmu.self_learning.datasets.boundary_aware_generator import generate_boundary_aware_samples
from jianmu.self_learning.datasets.boundary_curriculum import build_boundary_curriculum


def test_boundary_curriculum_has_all_stages():
    schedule = build_boundary_curriculum(generate_boundary_aware_samples(600, seed=1))
    assert schedule["curriculum_stage_count"] == 6
    assert "stage_5_mixed_boundary_stress" in schedule["stage_sample_counts"]
