from jianmu.self_learning.darwinforge.longhaul_compiler_validation import run_longhaul_compiler_validation


def test_longhaul_compiler_validation_uses_real_cl(tmp_path):
    result = run_longhaul_compiler_validation(tmp_path, target=4, compile_worker_count=2)
    assert result["real_compiler_invocation_count"] == 4
    assert result["compiler_validation_clean"] is True
