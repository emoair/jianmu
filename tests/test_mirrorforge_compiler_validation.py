from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_compiler_validation import run_mirrorforge_compiler_validation


def test_mirrorforge_compiler_validation_uses_real_cl(tmp_path) -> None:
    result = run_mirrorforge_compiler_validation(tmp_path, target=4, compile_worker_count=2)
    assert result["compiler_name"] == "cl"
    assert result["real_compiler_invocation_count"] == 4
