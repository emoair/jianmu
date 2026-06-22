from jianmu.self_learning.darwinforge.redqueen_multiround_stability_schema import RedQueenStabilityConfig, build_multiround_stability_config_record
from jianmu.self_learning.darwinforge.redqueen_stability_cycle_runner import run_stability_cycles
from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import build_weak_signal_scenarios


def test_redqueen_stability_cycle_runner_runs_eight_cycles(tmp_path):
    cfg = RedQueenStabilityConfig(total_events_target=1600, minimum_real_compiler_invocations=600)
    schedule = build_multiround_stability_config_record(cfg)["weak_signal_schedule"]
    preflight = {"compiler_environment_ready": True, "msvc_preflight_passed": True, "fail_fast_triggered": False, "cl_found": True, "link_found": True}
    plan = {"category_weights": {}, "difficulty_levels": {"function": 2, "structured_recursion": 2}, "active_review_allocations": {}, "shape_diversity_targets": {}, "boundary_recheck_targets": {}, "rollback_recheck_targets": {}, "replay_recheck_targets": {}}
    result = run_stability_cycles(tmp_path, plan, build_weak_signal_scenarios(), cfg, schedule, preflight)
    assert result["cycles_completed"] == 8
    assert (tmp_path / "cycles" / "cycle_0" / "cycle_msvc_guard.json").exists()
