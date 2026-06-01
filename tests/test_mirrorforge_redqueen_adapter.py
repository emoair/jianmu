from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_redqueen_adapter import build_mirrorforge_redqueen_adapter


def test_mirrorforge_redqueen_adapter_failure_categories() -> None:
    result = build_mirrorforge_redqueen_adapter()
    assert "token_to_ir_failure" in result["failure_categories"]
    assert result["redqueen_only_adjusts_curriculum"]
