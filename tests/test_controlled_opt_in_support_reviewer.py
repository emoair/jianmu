from jianmu.self_learning.darwinforge.controlled_opt_in_support_reviewer import build_reviewer_support_pack


def test_trace_review_generates_reviewer_pack(tmp_path):
    result = build_reviewer_support_pack(tmp_path, {"recommended_claim_level": "controlled_opt_in_support_candidate_ready"})
    assert result["reviewer_support_pack_generated"] is True
    assert (tmp_path / "reviewer_support_pack" / "REVIEWER_README.md").exists()
    assert (tmp_path / "reviewer_support_pack" / "REVIEW_CHECKLIST.md").exists()
