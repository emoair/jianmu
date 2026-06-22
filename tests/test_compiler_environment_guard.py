from jianmu.self_learning.darwinforge.compiler_environment_guard import build_msvc_fail_fast_test, validation_can_start


def test_compiler_environment_guard_blocks_validation_without_cl(tmp_path):
    result = build_msvc_fail_fast_test(tmp_path)
    assert result["validation_started"] is False
    assert result["msvc_fail_fast_test_passed"] is True
    assert validation_can_start({"compiler_environment_ready": False, "msvc_preflight_passed": False, "fail_fast_triggered": True}) is False
