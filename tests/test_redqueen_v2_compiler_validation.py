from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_compiler_validation import build_redqueen_v2_compiler_validation


def test_compiler_validation_uses_real_cl(tmp_path) -> None:
    result = build_redqueen_v2_compiler_validation(tmp_path)
    assert result["backend_type"] == "real_c_compiler"
    assert result["compiler_name"] == "cl"
