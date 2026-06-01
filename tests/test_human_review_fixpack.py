from jianmu.self_learning.darwinforge.human_review_fixpack import generate_human_review_fixpack


def test_human_review_fixpack_generated(tmp_path):
    result = generate_human_review_fixpack(tmp_path)
    assert result["human_review_fixpack_completed"] is True
    assert (tmp_path / "human_review_fixpack" / "claim_wording_fixpack.md").exists()


def test_human_review_completed_false(tmp_path):
    result = generate_human_review_fixpack(tmp_path)
    assert result["human_review_completed"] is False
    assert result["ready_for_v1_0_release"] is False
