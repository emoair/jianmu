from jianmu.self_learning.darwinforge.turing_frontier_compiler_validation import compiler_validation


def test_turing_frontier_compiler_validation_uses_real_cl(tmp_path):
    result = compiler_validation(tmp_path, target=4, compile_worker_count=2)
    assert result["real_compiler_invocation_count"] == 4
    assert result["compiler_validation_clean"] is True
    assert result["future_domain_compiled_count"] == 0
