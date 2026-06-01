from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_compiler_validation import run_codecartographer_compiler_validation


def test_codecartographer_compiler_validation_uses_real_cl(tmp_path):
    result = run_codecartographer_compiler_validation(tmp_path, target=8, compile_worker_count=1)
    assert result["compiler_name"] == "cl"
    assert result["real_compiler_invocation_count"] == 8
