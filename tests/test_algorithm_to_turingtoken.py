from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_to_turingtoken import source_to_turingtoken


def test_algorithm_to_turingtoken_for_counter_machine() -> None:
    token = source_to_turingtoken("counter_machine_mini_project", "int compute(void){return 0;}")
    assert "COUNTER_MACHINE" in token["token_sequence"]

