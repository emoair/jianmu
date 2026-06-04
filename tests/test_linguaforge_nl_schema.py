from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_nl_schema import build_linguaforge_row


def test_linguaforge_nl_schema_outputs_chinese_token_row() -> None:
    row = build_linguaforge_row("pilot", 0)
    assert row["language"] == "zh"
    assert "声明变量" in row["nl_text"]
    assert row["target_token"]["token_type"] == "StandardToken"
    assert row["leakage_guard"]["nl_contains_c_source"] is False

