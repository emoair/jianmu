from __future__ import annotations

from jianmu.self_learning.darwinforge.projectcartographer_schema import project_ir_for, project_source_for
from jianmu.self_learning.darwinforge.projectcartographer_to_mirrortoken import source_to_mirrortoken


def test_project_to_mirrortoken_has_program_bounds() -> None:
    token = source_to_mirrortoken(project_ir_for(0, "single_function_mini_project"), "single_function_mini_project", project_source_for(0, "single_function_mini_project"))
    assert token["token_sequence"][0] == "PROGRAM_BEGIN"
    assert token["token_sequence"][-1] == "PROGRAM_END"

