from jianmu.self_learning.darwinforge.redqueen_linear_difficulty_scheduler import build_linear_difficulty_schedule


def test_redqueen_difficulty_scheduler_stable_category_anneals(tmp_path):
    result = build_linear_difficulty_schedule(tmp_path, {"categories": [{"category": "structured_recursion", "success_rate": 1.0, "wrong_stdout_rate": 0, "timeout_rate": 0, "coverage_gap": 0, "repeated_shape_risk": "low"}]})
    row = result["schedule"][0]
    assert row["stability_state"] == "stable"
    assert row["next_difficulty_level"] == 2


def test_redqueen_difficulty_scheduler_weak_category_gets_more_basic_samples(tmp_path):
    result = build_linear_difficulty_schedule(tmp_path, {"categories": [{"category": "function", "success_rate": 0.9, "wrong_stdout_rate": 0, "timeout_rate": 0, "coverage_gap": 0, "repeated_shape_risk": "low"}]})
    row = result["schedule"][0]
    assert row["stability_state"] == "weak"
    assert row["sample_push_weight_delta"] > 0
