from jianmu.self_learning.darwinforge.opt_active_work_rate import ActiveWorkRateTracker


def test_opt_active_work_rate_reports_delta_and_rate() -> None:
    tracker = ActiveWorkRateTracker()
    first = tracker.payload(elapsed_seconds=10, frontend_total=20, backend_cl_total=5, backend_link_total=5, backend_exe_total=5)
    second = tracker.payload(elapsed_seconds=20, frontend_total=40, backend_cl_total=15, backend_link_total=15, backend_exe_total=15)
    assert first["backend_cl_delta"] == 5
    assert second["backend_cl_delta"] == 10
    assert second["backend_rate_per_min"] > 0
    assert second["active_state"] == "active_backend"
