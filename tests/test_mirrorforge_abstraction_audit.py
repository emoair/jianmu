from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_abstraction_audit import run_abstraction_leakage_audit
from jianmu.self_learning.darwinforge.mirrorforge_abstraction_variants import build_abstraction_variant_dataset
from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset


def test_mirrorforge_abstraction_leakage_audit(tmp_path):
    source = tmp_path / "source"
    variants = tmp_path / "variants"
    records = tmp_path / "records"
    build_mirrorforge_dataset(source, minimum_samples=20, counts_by_scale={"pilot": 20})
    build_abstraction_variant_dataset(source, variants, variants=["lossless", "semantic"])
    result = run_abstraction_leakage_audit(variants, {"abstraction_risk_score": 0.4, "target_ir_structure_similarity_score": 1.0}, records)
    assert result["leakage_audit_passed"] is True
    assert result["mirror_token_contains_raw_target_ir_json_count"] == 0
