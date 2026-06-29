from jianmu.self_learning.darwinforge.incremental_dataset_schema import DATASET_CATEGORIES, IncrementalDatasetConfig, split_for_index


def test_incremental_dataset_schema() -> None:
    cfg = IncrementalDatasetConfig(target_dataset_samples=100, minimum_dataset_samples=50)
    assert "function-array" in DATASET_CATEGORIES
    assert split_for_index(0, 100, cfg) == "train"
    assert split_for_index(90, 100, cfg) == "replay"
    assert split_for_index(95, 100, cfg) == "negative_boundary"
