from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_module_schema import project_standard_token_schema, required_sample_fields


def test_codecartographer_supported_subset_contract():
    schema = project_standard_token_schema()
    assert schema["token_version"] == "project_standard_token_v1"
    assert "bounded_for_loop" in schema["current_supported_features"]
    assert "recursion" in schema["unsupported_features"]
    assert "project_standard_token" in required_sample_fields()
