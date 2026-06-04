from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.forgecorpus_manual_dropin_audit import audit_manual_dropin


def test_manual_dropin_requires_license_metadata(tmp_path: Path) -> None:
    (tmp_path / "sample.c").write_text("int compute(void){return 1;}", encoding="utf-8")
    result = audit_manual_dropin(tmp_path)
    assert result["manual_dropin_dir_exists"] is True
    assert result["manual_dropin_audit_passed"] is False

