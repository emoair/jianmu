from jianmu.self_learning.darwinforge.redqueen_iteration_schema import RedQueenIterationConfig
from jianmu.self_learning.darwinforge.redqueen_plan_executor import execute_redqueen_plan


def _plan():
    return {
        "plan": {
            "category_weights": {"function": 1.0, "array": 1.0, "function_array": 1.0, "structured_recursion": 1.0, "mixed": 1.0, "default_blocking": 1.15, "unsupported_boundary": 1.15},
            "difficulty_levels": {"function": 2, "array": 2, "function_array": 2, "structured_recursion": 2, "mixed": 2, "default_blocking": 2, "unsupported_boundary": 2},
            "active_review_allocations": {"function": 1.0},
            "shape_diversity_targets": {},
        }
    }


def test_redqueen_plan_executor_follows_plan(tmp_path):
    cfg = RedQueenIterationConfig(iteration_events=1000, minimum_real_compiler_invocations=650)
    result = execute_redqueen_plan(tmp_path, _plan(), cfg)
    assert result["plan_execution_passed"] is True
    assert result["plan_follow_rate"] >= 0.95


def test_redqueen_plan_executor_blocks_default_profile_change(tmp_path):
    result = execute_redqueen_plan(tmp_path, _plan(), RedQueenIterationConfig(iteration_events=100, minimum_real_compiler_invocations=60))
    assert result["default_profile_unchanged"] is True
    assert result["real_promotion_enabled"] is False
    assert result["bridge_reachable_without_opt_in_count"] == 0
