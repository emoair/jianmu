from jianmu.self_learning.darwinforge.redqueen_endurance_cycle_runner import run_endurance_cycles
from jianmu.self_learning.darwinforge.redqueen_real_landing_schema import RedQueenEnduranceConfig


def test_redqueen_endurance_cycle_runner_runs_three_cycles(tmp_path):
    plan = {"category_weights": {"function": 1.0, "array": 1.0, "function_array": 1.0, "structured_recursion": 1.0, "mixed": 1.0, "default_blocking": 1.15, "unsupported_boundary": 1.15}, "difficulty_levels": {}, "active_review_allocations": {}, "shape_diversity_targets": {}, "boundary_recheck_targets": {}, "rollback_recheck_targets": {}, "replay_recheck_targets": {}}
    metrics = {"categories": [{"category": "function", "success_rate": 1.0, "wrong_stdout_rate": 0.0, "timeout_rate": 0.0, "replay_drift_rate": 0.0, "rollback_failure_rate": 0.0, "coverage_gap": 0.0, "repeated_shape_risk": "low"}]}
    result = run_endurance_cycles(tmp_path, plan, metrics, RedQueenEnduranceConfig(cycle_events_target=100, minimum_real_compiler_invocations=30))
    assert result["cycles_completed"] == 3
