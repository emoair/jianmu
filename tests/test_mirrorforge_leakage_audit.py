from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset
from jianmu.self_learning.darwinforge.mirrorforge_leakage_audit import run_mirrorforge_leakage_audit


def test_mirrorforge_leakage_audit_blocks_expected_output(tmp_path) -> None:
    build_mirrorforge_dataset(tmp_path, minimum_samples=300, counts_by_scale={"pilot": 300})
    audit = run_mirrorforge_leakage_audit(tmp_path)
    assert audit["mirror_token_contains_expected_output_count"] == 0
    assert audit["leakage_audit_passed"]


def test_mirrorforge_leakage_audit_blocks_c_source(tmp_path) -> None:
    build_mirrorforge_dataset(tmp_path, minimum_samples=300, counts_by_scale={"pilot": 300})
    audit = run_mirrorforge_leakage_audit(tmp_path)
    assert audit["mirror_token_contains_c_source_count"] == 0
