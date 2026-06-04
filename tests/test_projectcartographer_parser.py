from __future__ import annotations

from jianmu.self_learning.darwinforge.projectcartographer_parser import parse_project_module


def test_projectcartographer_parser_handles_controlled_small_project() -> None:
    parsed = parse_project_module("int a(void){return 1;} int compute(void){return a();}")
    assert parsed["parse_success"] is True
    assert parsed["module_boundary_detected"] is True
    assert parsed["function_count"] >= 2

