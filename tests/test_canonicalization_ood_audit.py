from jianmu.self_learning.darwinforge.canonicalization_ood_audit import audit_canonicalization_ood_sample, run_canonicalization_ood_audit


def test_canonicalization_ood_audit_detects_made_supported():
    sample = {"sample_id": "1", "input_text": "请输出五", "input_mode": "ood_unrelated"}
    row = audit_canonicalization_ood_sample(sample)
    assert row["canonical_changed"]
    assert row["canonical_contains_arithmetic_signal"]


def test_canonicalization_ood_audit_summary():
    summary = run_canonicalization_ood_audit([{"sample_id": "1", "input_text": "请输出五", "input_mode": "ood_unrelated"}])
    assert "canonicalizer_made_supported_count" in summary

