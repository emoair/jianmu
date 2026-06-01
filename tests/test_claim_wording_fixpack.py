from jianmu.self_learning.darwinforge.claim_wording_fixpack import build_claim_wording_fixpack


def test_claim_wording_fixpack(tmp_path):
    result = build_claim_wording_fixpack(tmp_path)
    assert result["claim_wording_fixpack_completed"] is True
    assert (tmp_path / "claim_wording_fixpack.md").exists()
