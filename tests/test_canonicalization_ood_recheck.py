from jianmu.self_learning.darwinforge.canonicalization_ood_recheck import run_canonicalization_ood_recheck


def test_canonicalization_ood_recheck_reports_slice_source():
    result = run_canonicalization_ood_recheck([{"sample_id": "1", "input_text": "hello", "input_mode": "ood_english"}], slice_source="unit")
    assert result["canonicalizer_audit_slice_source"] == "unit"


def test_canonicalization_ood_recheck_explains_not_reproduced():
    result = run_canonicalization_ood_recheck([{"sample_id": "1", "input_text": "hello", "input_mode": "ood_english"}])
    assert "reason_not_reproduced" in result

