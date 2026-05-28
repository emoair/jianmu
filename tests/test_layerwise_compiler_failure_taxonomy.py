from jianmu.self_learning.darwinforge.layerwise_compiler_failure_taxonomy import classify_layerwise_compiler_failure


def test_layerwise_compiler_failure_taxonomy_categories():
    assert classify_layerwise_compiler_failure({"exception_type": "PermissionError", "permission_error_stage": "permission_compile_spawn"}) == "permission_compile_spawn"
    assert classify_layerwise_compiler_failure({"exception_type": "TimeoutExpired", "timeout": True, "compile_success": False}) == "cl_or_link_toolchain_error"
    assert classify_layerwise_compiler_failure({"compile_success": True, "runtime_success": True, "compiler_verified_correct": False}) == "wrong_stdout"
