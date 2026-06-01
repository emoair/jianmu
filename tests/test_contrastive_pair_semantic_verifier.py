from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.contrastive_full_materializer import materialize_contrastive_full_dataset
from jianmu.self_learning.darwinforge.contrastive_pair_semantic_verifier import verify_contrastive_pairs


def test_contrastive_semantic_verifier(tmp_path) -> None:
    materialize_contrastive_full_dataset(tmp_path, counts_by_scale={"pilot": 3000}, minimum_materialized_samples=3000)
    rows = []
    for path in tmp_path.glob("*/*.jsonl"):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)
    result = verify_contrastive_pairs(rows)
    assert result["pair_integrity_passed"]
    assert result["same_semantics_output_same_rate"] == 1.0
