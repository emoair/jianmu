from jianmu.self_learning.darwinforge.idle_padding_detector import detect_idle_padding


def test_idle_padding_detector_detects_zero_delta_windows() -> None:
    rows = [
        {"phase": "active_backend_validation", "actual_elapsed_seconds": 0, "backend_cl_delta": 0, "backend_exe_delta": 0},
        {"phase": "active_backend_validation", "actual_elapsed_seconds": 10, "backend_cl_delta": 0, "backend_exe_delta": 0},
        {"phase": "active_backend_validation", "actual_elapsed_seconds": 20, "backend_cl_delta": 0, "backend_exe_delta": 0},
    ]
    result = detect_idle_padding(rows)
    assert result["idle_padding_detected"] is True


def test_idle_padding_detector_allows_cleanup_idle() -> None:
    rows = [{"phase": "cleanup", "actual_elapsed_seconds": 10, "backend_cl_delta": 0, "backend_exe_delta": 0, "last_backend_age_sec": 100}]
    result = detect_idle_padding(rows)
    assert result["idle_padding_detector_passed"] is True
