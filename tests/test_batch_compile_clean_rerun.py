from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy_clean_rerun import _validation_clean_from_metrics


def _base():
    return {
        "compiler_verified_correct_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
    }


def test_clean_rerun_validation_requires_zero_wrong_stdout():
    metrics = _base()
    metrics["wrong_stdout_count"] = 1
    assert _validation_clean_from_metrics(metrics) is False


def test_clean_rerun_validation_requires_zero_terminating_timeout():
    metrics = _base()
    metrics["timeout_count"] = 1
    assert _validation_clean_from_metrics(metrics) is False
