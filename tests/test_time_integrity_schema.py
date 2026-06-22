from jianmu.self_learning.darwinforge.time_integrity_schema import TIME_REPAIR_STILL_NOT_PROVEN, TimeRepairValidationConfig


def test_time_integrity_schema():
    cfg = TimeRepairValidationConfig()
    assert cfg.planned_wall_clock_hours == 2.0
    assert "production readiness" in TIME_REPAIR_STILL_NOT_PROVEN
