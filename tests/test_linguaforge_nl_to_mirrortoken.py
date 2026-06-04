from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_nl_to_mirrortoken import map_nl_to_mirrortoken


def test_linguaforge_nl_to_mirrortoken_bounds() -> None:
    token = map_nl_to_mirrortoken("如果x大于2就输出x。", sample_index=1)
    assert token["token_sequence"][0] == "PROGRAM_BEGIN"
    assert token["token_sequence"][-1] == "PROGRAM_END"

