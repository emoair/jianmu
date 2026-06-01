from __future__ import annotations

from jianmu.self_learning.darwinforge.contrastive_full_audit import audit_contrastive_full_dataset
from jianmu.self_learning.darwinforge.contrastive_full_materializer import materialize_contrastive_full_dataset


def test_contrastive_full_audit_pair_integrity(tmp_path) -> None:
    materialize_contrastive_full_dataset(tmp_path, counts_by_scale={"pilot": 3000}, minimum_materialized_samples=3000)
    audit = audit_contrastive_full_dataset(tmp_path)
    assert audit["pair_integrity_passed"]
    assert audit["pair_semantic_difference_verified_rate"] >= 0.99
    assert audit["audit_passed"]
