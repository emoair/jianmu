from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_to_mirrortoken import source_to_mirrortoken
from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import target_ir_for


def test_algorithm_to_mirrortoken_no_target_ir_json() -> None:
    token = source_to_mirrortoken(target_ir_for(7), "prefix_sum", "int compute(void){return 7;}")
    assert '"op"' not in token["token_text"]
    assert token["token_sequence"][0] == "PROGRAM_BEGIN"

