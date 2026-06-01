from jianmu.self_learning.darwinforge.freeze_candidate_claim_registry import run_claim_registry


def test_claim_registry_blocks_overclaims(tmp_path):
    registry = run_claim_registry(tmp_path)
    claims = {row["claim"]: row for row in registry["claims"]}
    assert claims["Turing completeness"]["allowed"] is False
    assert claims["production readiness"]["paper_safe"] is False
    assert claims["Symbiotic freeze-thaw co-training positive signal"]["allowed"] is True
