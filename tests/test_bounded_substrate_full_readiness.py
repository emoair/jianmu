from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_full_readiness import assess_bounded_substrate_full_readiness


def test_bounded_substrate_full_readiness_requires_signal_audit(tmp_path) -> None:
    result = assess_bounded_substrate_full_readiness(tmp_path, {"signal_audit_passed": False}, {}, {})
    assert result["recommended_claim_level"] == "failed"
    assert "Turing completeness" not in str(result)
