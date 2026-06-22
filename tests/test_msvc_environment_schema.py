from jianmu.self_learning.darwinforge.msvc_environment_schema import build_msvc_environment_record


def test_msvc_environment_schema():
    record = build_msvc_environment_record(cl_found=True, link_found=True, cl_version_detected=True, link_version_detected=True, vcvars_initialized=True, vswhere_detected=False, vcvars64_candidate_paths=(), shell_warning="")
    assert record["compiler_environment_ready"] is True
    assert record["msvc_preflight_passed"] is True
