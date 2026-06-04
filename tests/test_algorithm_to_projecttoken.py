from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_to_projecttoken import source_to_project_standardtoken
from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import algorithm_source


def test_algorithm_to_projecttoken_no_raw_c_source() -> None:
    source, _ = algorithm_source(0, "sorting", "bubble_sort")
    token = source_to_project_standardtoken(source, "bubble_sort", "row")
    assert "#include" not in token["token_text"]
    assert "int main" not in token["token_text"]

