from jianmu.self_learning.darwinforge.redqueen_multiround_governance_runner import run_multiround_governance
from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import RedQueenWeakSignalConfig, build_multiround_config_record, build_weak_signal_scenarios


def test_redqueen_multiround_governance_runner(tmp_path):
    config = RedQueenWeakSignalConfig(total_events_target=1000, minimum_real_compiler_invocations=300)
    schedule = build_multiround_config_record(config)["weak_signal_schedule"]
    plan = {"category_weights": {}, "difficulty_levels": {"function": 2, "structured_recursion": 2}, "active_review_allocations": {}, "shape_diversity_targets": {}, "boundary_recheck_targets": {}, "rollback_recheck_targets": {}, "replay_recheck_targets": {}}
    result = run_multiround_governance(tmp_path, plan, build_weak_signal_scenarios(), config, schedule)
    assert result["cycles_completed"] == 5
    assert (tmp_path / "cycles" / "cycle_1" / "cycle_weak_signal_injection.json").exists()
