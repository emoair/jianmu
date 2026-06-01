from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.codecartographer_module_descriptor import build_module_descriptor
from jianmu.self_learning.darwinforge.codecartographer_module_parser import parse_code_module


def test_codecartographer_module_descriptor_features():
    descriptor = build_module_descriptor(parse_code_module(Path("examples/codecartographer_fixtures/module_function_array.c")))
    assert descriptor["module_descriptor"]["module_category"] == "function_array_module"
    assert descriptor["feature_classification_descriptor"]["has_array"] is True
    assert descriptor["feature_classification_descriptor"]["has_function"] is True
