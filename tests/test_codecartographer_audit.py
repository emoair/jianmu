from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_audit import audit_codecartographer_dataset
from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import build_codecartographer_dataset


def test_codecartographer_audit(tmp_path):
    dataset = tmp_path / "dataset"
    records = tmp_path / "records"
    build_codecartographer_dataset(dataset, minimum_samples=100, counts_by_scale={"pilot": 100})
    result = audit_codecartographer_dataset(dataset, records)
    assert result["audit_passed"] is True
    assert result["token_contains_c_source_count"] == 0
