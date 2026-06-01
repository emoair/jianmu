from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.codecartographer_module_parser import parse_code_module


def test_codecartographer_module_parser_supported_fixture():
    parsed = parse_code_module(Path("examples/codecartographer_fixtures/module_bounded_control.c"))
    assert parsed["parse_success"] is True
    assert parsed["classification"]["support_status"] == "current_supported"
    assert parsed["features"]["has_for_loop"] is True


def test_codecartographer_module_parser_unsupported_fixture():
    parsed = parse_code_module(Path("examples/codecartographer_fixtures/module_unsupported_features.c"))
    assert parsed["classification"]["support_status"] == "unsupported"
    assert "recursion" in parsed["classification"]["unsupported_features"]
