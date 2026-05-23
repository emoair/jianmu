from jianmu.self_learning.darwinforge.mandatory_counter_guard import assess_mandatory_counters


def _good():
    return {
        "reported_train_count": 1,
        "actual_train_iterated_count": 1,
        "reported_eval_count": 1,
        "actual_eval_iterated_count": 1,
        "reported_external_ood_count": 1,
        "actual_external_ood_iterated_count": 1,
        "freebeam_eval_call_count": 2,
        "canonicalizer_call_count": 3,
        "branchchain_route_call_count": 3,
        "runtime_capture_event_count": 1,
        "cross_process_child_eval_count": 1,
        "synthetic_summary_detected": False,
        "fixed_metric_detected": False,
    }


def test_mandatory_counter_guard_blocks_zero_loop():
    counters = _good()
    counters["actual_train_iterated_count"] = 0
    result = assess_mandatory_counters(counters, 0.1)
    assert result["mandatory_counter_guard_passed"] is False
    assert result["mode_status"] == "invalid"


def test_mandatory_counter_guard_requires_eval_calls():
    counters = _good()
    counters["freebeam_eval_call_count"] = 0
    result = assess_mandatory_counters(counters, 0.1)
    assert result["mandatory_counter_guard_passed"] is False
    assert "freebeam_eval_call_count must be > 0" in result["blocking_issues"]
