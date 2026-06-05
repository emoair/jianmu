from jianmu.self_learning.darwinforge.csystems_dataset_builder import build_csystems_dataset, iter_csystems_rows


def test_csystems_dataset_builder(tmp_path):
    result = build_csystems_dataset(tmp_path / "ds", "pilot", seed=182)
    assert result["dataset_generated"] is True
    assert result["total_samples"] == 100_000
    assert next(iter_csystems_rows(tmp_path / "ds"))["dataset_version"] == "v1.0.4_csystems_frontier"
