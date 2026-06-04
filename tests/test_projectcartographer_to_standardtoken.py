from __future__ import annotations

from jianmu.self_learning.darwinforge.projectcartographer_schema import project_source_for
from jianmu.self_learning.darwinforge.projectcartographer_to_standardtoken import source_to_project_standardtoken


def test_project_standardtoken_does_not_contain_c_source() -> None:
    source = project_source_for(0, "single_function_mini_project")
    token = source_to_project_standardtoken(source, "single_function_mini_project", "row")
    assert token["token_type"] == "project_standardtoken"
    assert "#include" not in token["token_text"]
    assert "int main" not in token["token_text"]

