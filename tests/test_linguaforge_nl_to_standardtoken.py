from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_nl_to_standardtoken import map_nl_to_standardtoken


def test_linguaforge_nl_to_standardtoken_no_c_or_ir() -> None:
    token = map_nl_to_standardtoken("声明变量x为3，最后输出x。")
    assert token["token_type"] == "StandardToken"
    assert "int main" not in token["token_text"]
    assert '"op"' not in token["token_text"]

