from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import build_codecartographer_dataset


def test_codecartographer_dataset_shards_under_45mb(tmp_path):
    summary = build_codecartographer_dataset(tmp_path / "dataset", minimum_samples=100, counts_by_scale={"pilot": 100})
    assert summary["codecartographer_dataset_generated"] is True
    assert summary["max_shard_size_mb"] < 45
    assert (tmp_path / "dataset" / "pilot" / "manifest.json").exists()
