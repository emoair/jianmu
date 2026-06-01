from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset


def test_mirrorforge_dataset_shards_under_45mb(tmp_path) -> None:
    result = build_mirrorforge_dataset(tmp_path, minimum_samples=300, counts_by_scale={"pilot": 300})
    assert result["mirrorforge_dataset_generated"]
    assert result["max_shard_size_mb"] <= 45
