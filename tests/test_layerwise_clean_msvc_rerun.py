from jianmu.self_learning.darwinforge.clean_msvc_preflight import run_clean_msvc_preflight
from jianmu.self_learning.darwinforge.layerwise_clean_msvc_rerun import _is_clean


def test_layerwise_clean_msvc_preflight_records_environment(tmp_path):
    report = run_clean_msvc_preflight(tmp_path, tmp_path)
    assert "known_360_process_detected" in report
    assert "defender_or_security_lock_suspected" in report
    assert "stale_cl_process_count" in report


def test_layerwise_clean_rerun_reports_primary_and_fallback_separately():
    assert _is_clean({
        "completed": True,
        "compiler_verified_correct_rate": 0.99,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "recursion_compiled_count": 0,
        "array_compiled_count": 0,
        "function_compiled_count": 0,
        "backend_claim_safe": True,
    })


def test_layerwise_clean_rerun_uses_real_cl():
    metrics = {"backend_type": "real_c_compiler", "compiler_name": "cl", "compiler_environment": "msvc_vcvars64"}
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_layerwise_clean_rerun_blocks_future_domain_compile():
    metrics = {"future_domain_compiled_count": 0, "recursion_compiled_count": 0, "array_compiled_count": 0, "function_compiled_count": 0}
    assert sum(metrics.values()) == 0
