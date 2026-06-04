from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_substrate_lock_audit import substrate_lock_audit


def test_linguaforge_substrate_lock_audit_no_promotion() -> None:
    audit = substrate_lock_audit("records")
    assert audit["real_promotion_enabled"] is False
    assert audit["default_profile_unchanged"] is True

