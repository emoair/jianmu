from __future__ import annotations

from jianmu.self_learning.darwinforge.projectcartographer_to_turingtoken import source_to_turingtoken


def test_project_to_turingtoken_counter_machine_witness() -> None:
    token = source_to_turingtoken("counter_machine_mini_project", "int compute(void){return 0;}")
    assert "COUNTER_MACHINE" in token["token_sequence"]
    assert token["token_type"] == "turingtoken"

