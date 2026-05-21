import json
from pathlib import Path

import pytest

from jianmu.self_learning.datasets.sharded_dataset_loader import load_dataset_split_with_report, write_sharded_manifest


def test_sharded_loader_loads_single_jsonl(tmp_path):
    path = tmp_path / "train.jsonl"
    path.write_text(json.dumps({"sample_id": "s1"}) + "\n", encoding="utf-8")
    report = load_dataset_split_with_report(path)
    assert report["source_type"] == "single_file"
    assert report["loaded_count"] == 1


def test_sharded_loader_loads_manifest(tmp_path):
    manifest = write_sharded_manifest([{"sample_id": "s1"}, {"sample_id": "s2"}], tmp_path, "train", shard_size=1)
    report = load_dataset_split_with_report(manifest["manifest_path"])
    assert report["source_type"] == "sharded_manifest"
    assert report["shard_count"] == 2
    assert report["loaded_count"] == 2


def test_sharded_loader_reports_missing_shard(tmp_path):
    manifest = write_sharded_manifest([{"sample_id": "s1"}], tmp_path, "train", shard_size=1)
    Path(tmp_path / "train-part-00000.jsonl").unlink()
    with pytest.raises(FileNotFoundError):
        load_dataset_split_with_report(manifest["manifest_path"])
