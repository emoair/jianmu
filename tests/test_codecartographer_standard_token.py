from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.codecartographer_module_descriptor import build_module_descriptor
from jianmu.self_learning.darwinforge.codecartographer_module_parser import parse_code_module
from jianmu.self_learning.darwinforge.codecartographer_standard_token import descriptor_to_standard_token, token_contains_c_source, token_has_raw_target_ir


def test_project_standardtoken_not_raw_target_ir():
    token = descriptor_to_standard_token(build_module_descriptor(parse_code_module(Path("examples/codecartographer_fixtures/module_arithmetic_core.c"))))
    assert token_has_raw_target_ir(token) is False
    assert '"op"' not in token["token_text"]


def test_project_standardtoken_no_c_source_leakage():
    token = descriptor_to_standard_token(build_module_descriptor(parse_code_module(Path("examples/codecartographer_fixtures/module_bounded_control.c"))))
    assert token_contains_c_source(token) is False
    assert "MODULE_BEGIN" in token["token_sequence"]
