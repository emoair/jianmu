from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_v2_large_compiler_validation import run_redqueen_v2_large_compiler_validation


def test_compiler_validation_uses_real_cl(tmp_path) -> None:
    result = run_redqueen_v2_large_compiler_validation(tmp_path, target=4, compile_worker_count=2)
    assert result["backend_type"] == "real_c_compiler"
    assert result["compiler_name"] == "cl"
    assert result["real_compiler_invocation_count"] == 4
