from jianmu.self_learning.darwinforge.incremental_dataset_schema import IncrementalDatasetConfig
from jianmu.self_learning.darwinforge.streaming_dataset_writer import iter_incremental_samples, write_streaming_dataset


def test_streaming_dataset_writer_does_not_store_all_samples(tmp_path) -> None:
    cfg = IncrementalDatasetConfig(target_dataset_samples=30, minimum_dataset_samples=10, evidence_count=3)
    schedule = {"category_weights": {}}
    result = write_streaming_dataset(tmp_path / "records", tmp_path / "artifacts", cfg, schedule, {})
    assert result["no_giant_sample_list"] is True
    assert result["streaming_dataset_writer_passed"] is True
    assert iter(iter_incremental_samples(2, cfg, schedule)) is not None
    assert len(list((tmp_path / "records" / "dataset_evidence_pack").glob("*"))) == 3
