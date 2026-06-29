from jianmu.self_learning.darwinforge.dataset_mirror_feedback import build_mirror_dataset_feedback
from jianmu.self_learning.darwinforge.dataset_redqueen_scheduler import build_redqueen_dataset_schedule
from jianmu.self_learning.darwinforge.incremental_curriculum_dataset_builder import build_incremental_curriculum_dataset
from jianmu.self_learning.darwinforge.incremental_dataset_schema import IncrementalDatasetConfig


def test_incremental_dataset_builder_creates_splits(tmp_path) -> None:
    schedule = build_redqueen_dataset_schedule(tmp_path / "records")
    mirror = build_mirror_dataset_feedback(tmp_path / "records", schedule)
    result = build_incremental_curriculum_dataset(tmp_path / "records", tmp_path / "artifacts", IncrementalDatasetConfig(target_dataset_samples=100, minimum_dataset_samples=50, evidence_count=10), schedule, mirror)
    assert result["dataset_training_passed"] is True
    assert result["train_samples"] == 70
    assert result["heldout_samples"] == 15
    assert result["dataset_evidence_pack_passed"] is True
