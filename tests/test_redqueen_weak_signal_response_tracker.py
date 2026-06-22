from jianmu.self_learning.darwinforge.redqueen_weak_signal_response_tracker import audit_weak_signal_response


def _cycle(index, function_count=10, mixed_review=1.0, function_review=1.0, function_difficulty=2, signals=None):
    return {
        "cycle_index": index,
        "plan": {"shape_diversity_targets": {"function": index == 1}, "replay_recheck_targets": {"mixed": index == 2}, "boundary_recheck_targets": {"mixed": index == 2}},
        "injection": {"injections": signals or []},
        "execution": {
            "actual_category_distribution": {"function": function_count},
            "actual_review_allocation": {"function": function_review, "mixed": mixed_review},
            "actual_difficulty_distribution": {"function": function_difficulty, "structured_recursion": 2},
            "wrong_stdout_count": 0,
        },
    }


def test_weak_signal_response_tracker_boosts_function():
    cycles = [_cycle(0), _cycle(1, function_count=15, function_review=1.2, function_difficulty=1, signals=[{"scenario_id": "function_call_weak_signal"}]), _cycle(2, mixed_review=1.3, signals=[{"scenario_id": "mixed_integration_weak_signal"}]), _cycle(4)]
    result = audit_weak_signal_response(cycles)
    assert result["function_sample_weight_increased"] is True
    assert result["function_active_review_increased"] is True
    assert result["weak_signal_response_audit_passed"] is True


def test_weak_signal_response_tracker_boosts_mixed_replay():
    cycles = [_cycle(0), _cycle(1, function_count=15, function_review=1.2, function_difficulty=1, signals=[{"scenario_id": "function_call_weak_signal"}]), _cycle(2, mixed_review=1.3, signals=[{"scenario_id": "mixed_integration_weak_signal"}]), _cycle(4)]
    result = audit_weak_signal_response(cycles)
    assert result["mixed_active_review_increased"] is True
    assert result["mixed_replay_recheck_increased"] is True
    assert result["mixed_boundary_stress_increased"] is True


def test_stable_recursion_does_not_fabricate_weak_signal():
    cycles = [_cycle(0), _cycle(1, function_count=15, function_review=1.2, function_difficulty=1, signals=[{"scenario_id": "function_call_weak_signal"}]), _cycle(2, mixed_review=1.3, signals=[{"scenario_id": "mixed_integration_weak_signal"}]), _cycle(4)]
    result = audit_weak_signal_response(cycles)
    assert result["recursion_weak_signal_fabricated"] is False
    assert result["recursion_stable_annealing_applied"] is True
