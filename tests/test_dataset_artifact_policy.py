from jianmu.self_learning.datasets.dataset_artifact_policy import DatasetArtifactPolicy, check_dataset_artifacts


def test_artifact_policy_detects_oversized_files(tmp_path):
    path = tmp_path / "big.jsonl"
    path.write_bytes(b"x" * 2048)
    report = check_dataset_artifacts(tmp_path, DatasetArtifactPolicy(max_file_size_mb_for_git=0, prefer_shards_above_mb=0))
    assert report["oversized_file_count"] == 1
    assert report["blocking_issue_count"] == 1


def test_artifact_policy_recommends_sharding(tmp_path):
    path = tmp_path / "big.jsonl"
    path.write_bytes(b"x" * 2048)
    report = check_dataset_artifacts(tmp_path, DatasetArtifactPolicy(max_file_size_mb_for_git=100, prefer_shards_above_mb=0))
    assert report["should_shard"] is True
    assert report["lfs_recommended"] is False
