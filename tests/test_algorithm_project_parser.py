from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_project_parser import parse_project_module
from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import algorithm_source


def test_algorithm_parser_handles_sorting_and_search() -> None:
    for family, name in [("sorting", "insertion_sort"), ("search", "linear_search")]:
        source, _ = algorithm_source(4, family, name)
        parsed = parse_project_module(source)
        assert parsed["parse_success"] is True

