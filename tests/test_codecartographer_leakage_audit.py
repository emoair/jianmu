from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import build_codecartographer_dataset
from jianmu.self_learning.darwinforge.codecartographer_leakage_audit import run_codecartographer_leakage_audit


def test_codecartographer_leakage_audit(tmp_path):
    dataset = tmp_path / "dataset"
    build_codecartographer_dataset(dataset, minimum_samples=100, counts_by_scale={"pilot": 100})
    result = run_codecartographer_leakage_audit(dataset, tmp_path / "records")
    assert result["leakage_audit_passed"] is True
    assert result["token_contains_raw_target_ir_json_count"] == 0
