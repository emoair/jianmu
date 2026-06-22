from jianmu.self_learning.darwinforge.redqueen_two_lane_metrics import build_two_lane_metrics, real_compile_lane_is_clean


def test_two_lane_metrics_keeps_real_correctness_separate():
    metrics = build_two_lane_metrics(
        {"compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "timeout_count": 0},
        {"weak_signal_is_synthetic": True, "synthetic_success_rate": 0.965},
    )
    assert metrics["weak_signal_affects_real_correctness"] is False
    assert metrics["synthetic_signal_affected_real_lane"] is False
    assert real_compile_lane_is_clean(metrics) is True
