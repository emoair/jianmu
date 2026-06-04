from __future__ import annotations

from jianmu.self_learning.darwinforge.forgecorpus_license_audit import audit_license


def test_license_audit_allows_permissive() -> None:
    result = audit_license({"source_kind": "manual_dropin", "source_url": "u", "source_commit": "c", "file_path": "f.c", "source_hash": "h", "license": "MIT"})
    assert result["allowed_for_training"] is True


def test_license_audit_quarantines_unknown_and_gpl() -> None:
    for license_name in ("unknown", "GPL"):
        result = audit_license({"source_kind": "manual_dropin", "source_url": "u", "source_commit": "c", "file_path": "f.c", "source_hash": "h", "license": license_name})
        assert result["allowed_for_training"] is False

