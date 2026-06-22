from jianmu.self_learning.darwinforge.time_integrity_schema import TimeRepairValidationConfig
from jianmu.self_learning.darwinforge.wallclock_repair_validation import run_wallclock_repair_validation


def test_wallclock_repair_validation(tmp_path):
    cfg = TimeRepairValidationConfig(planned_wall_clock_hours=0.000001, cycles=1, planned_cycle_min_hours=0.000001, target_events=100, minimum_events=50, minimum_real_compiler_invocations=30, heartbeat_interval_events=1, idle_grace_seconds=0)
    plan = {"category_weights": {}, "difficulty_levels": {}, "active_review_allocations": {}, "shape_diversity_targets": {}, "boundary_recheck_targets": {}, "rollback_recheck_targets": {}, "replay_recheck_targets": {}}
    result = run_wallclock_repair_validation(tmp_path, tmp_path, plan, cfg)
    assert result["summary"]["repair_validation_passed"] is True
    assert result["summary"]["planned_duration_used_as_actual"] is False
