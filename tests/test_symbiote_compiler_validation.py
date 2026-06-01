from jianmu.self_learning.darwinforge.symbiote_compiler_validation import run_symbiote_compiler_validation


def test_symbiote_compiler_validation_uses_real_cl(tmp_path):
    result = run_symbiote_compiler_validation(tmp_path, target=8, compile_worker_count=1)
    assert result["real_compiler_invocation_count"] == 8
    assert result["compiler_verified_correctness_rate"] >= 0.99
