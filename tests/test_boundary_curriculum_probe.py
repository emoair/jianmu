from jianmu.self_learning.darwinforge.boundary_curriculum_probe import run_boundary_curriculum_probe
from jianmu.self_learning.datasets.boundary_scale_builder import build_boundary_scale


def test_boundary_probe_loads_dataset(tmp_path):
    summary = build_boundary_scale("small", tmp_path, seed=3)
    probe = run_boundary_curriculum_probe(summary["output_dir"])
    assert probe["dataset_load_success"]


def test_boundary_probe_validates_reward_policy(tmp_path):
    summary = build_boundary_scale("small", tmp_path, seed=4)
    probe = run_boundary_curriculum_probe(summary["output_dir"])
    assert probe["boundary_reward_policy_valid"]
