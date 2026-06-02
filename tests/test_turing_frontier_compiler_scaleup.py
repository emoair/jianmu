from jianmu.self_learning.darwinforge.turing_frontier_compiler_scaleup import run_compiler_scaleup


def test_compiler_scaleup_uses_real_cl(tmp_path):
    result = run_compiler_scaleup(tmp_path, target=4, compile_worker_count=2)
    assert result["real_compiler_invocation_count"] == 4
    assert result["compiler_validation_clean"] is True
    assert result["recursion_compiled_count"] == 0
