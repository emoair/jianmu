from jianmu.self_learning.darwinforge.source_review_claim_boundary_fix import write_claim_boundary_fix_report


def test_claim_boundary_fix_report(tmp_path):
    result = write_claim_boundary_fix_report(tmp_path)
    assert result["claim_boundary_fix_completed"] is True
    assert result["production_function_support_completed"] is False
    assert result["real_promotion_disabled"] is True

