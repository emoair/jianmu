from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_contrastive_adapter import build_mirrorforge_contrastive_adapter


def test_mirrorforge_contrastive_adapter_reuses_logic() -> None:
    result = build_mirrorforge_contrastive_adapter()
    assert result["uses_existing_contrastive_logic"]
