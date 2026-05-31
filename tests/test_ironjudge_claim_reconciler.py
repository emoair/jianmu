from __future__ import annotations

from jianmu.self_learning.darwinforge.ironjudge_claim_reconciler import reconcile_claim


def test_ironjudge_claim_reconciler_no_overclaim() -> None:
    result = reconcile_claim("ironjudge_20k_clean_frontier_evidence_strengthened", True, True, False, False, False, False, True, True)
    assert result["recommended_claim_level"] == "ironjudge_5k_clean_needs_20k_reconciled"
    assert result["v0_9_18_1_claim_was_overstated"] is True
