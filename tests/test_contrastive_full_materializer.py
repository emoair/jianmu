from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.contrastive_full_materializer import materialize_contrastive_full_dataset


def test_contrastive_full_materializer_outputs_splits(tmp_path) -> None:
    result = materialize_contrastive_full_dataset(tmp_path, counts_by_scale={"pilot": 3000, "medium": 3000, "large": 3000}, minimum_materialized_samples=9000)
    assert result["full_contrastive_materialization_completed"]
    for scale in ["pilot", "medium", "large"]:
        scale_dir = tmp_path / scale
        assert (scale_dir / "train.jsonl").exists()
        assert (scale_dir / "eval.jsonl").exists()
        assert (scale_dir / "test.jsonl").exists()
        assert (scale_dir / "heldout.jsonl").exists()
        manifest = json.loads((scale_dir / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["materialized_count"] == 3000
