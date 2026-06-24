from jianmu.self_learning.darwinforge.mirror_redqueen_time_integrity_guard import audit_true_time_integrity


def test_true_time_integrity_audit_rejects_planned_as_actual(tmp_path) -> None:
    run = {"planned_wall_clock_hours": 8, "actual_wall_clock_hours": 1, "actual_elapsed_seconds": 3600, "minimum_satisfied_by": "actual_monotonic_elapsed", "monotonic_start": 1.0, "monotonic_end": 2.0, "utc_start_time": "a", "utc_end_time": "b"}
    heartbeat = {"heartbeat_records_written": 1, "heartbeat_span_matches_actual_elapsed": True}
    cycles = [{"time": {"actual_cycle_elapsed_seconds": 3600}}]
    result = audit_true_time_integrity(tmp_path, run, cycles, heartbeat)
    assert result["true_time_integrity_audit_passed"] is False
    assert result["planned_time_used_as_actual"] is False

