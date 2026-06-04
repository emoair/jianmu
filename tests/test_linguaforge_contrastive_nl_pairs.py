from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_contrastive_nl_pairs import build_contrastive_pairs


def test_linguaforge_contrastive_pairs_include_boundary_difference() -> None:
    pairs = build_contrastive_pairs()
    assert pairs
    assert any("没有明确次数" in b for _, b in pairs)

