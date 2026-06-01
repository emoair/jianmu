from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset
from jianmu.self_learning.darwinforge.mirrorforge_ir_similarity_audit import run_ir_similarity_audit


def test_mirrorforge_ir_similarity_audit(tmp_path):
    source = tmp_path / "source"
    records = tmp_path / "records"
    build_mirrorforge_dataset(source, minimum_samples=20, counts_by_scale={"pilot": 20})
    result = run_ir_similarity_audit(source, records)
    assert result["ir_similarity_audit_completed"] is True
    assert result["raw_target_ir_json_overlap_count"] == 0
    assert 0 <= result["abstraction_risk_score"] <= 1
