from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_paraphrase_generator import generate_chinese_paraphrases


def test_linguaforge_paraphrase_generator_returns_chinese_variants() -> None:
    variants = generate_chinese_paraphrases("声明变量x为3，最后输出x。")
    assert len(variants) >= 4
    assert all(any("\u4e00" <= ch <= "\u9fff" for ch in item) for item in variants)

