from jianmu.self_learning.darwinforge.arithmetic_heldout_eval import REQUIRED_HELDOUT_STAGES, evaluate_heldout_arithmetic


def test_arithmetic_heldout_eval_has_required_stages():
    rows = [
        {"id": stage, "category": "current_supported_arithmetic", "stage": stage, "provenance": {"generation_rule": stage}, "expected_output": "1\n"}
        for stage in REQUIRED_HELDOUT_STAGES
    ]
    result = evaluate_heldout_arithmetic(rows, learned_strength=1.0)
    assert set(result["by_stage"]) == set(REQUIRED_HELDOUT_STAGES)
    assert result["by_stage"]["precedence"]["sample_count"] == 1
