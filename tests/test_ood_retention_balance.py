from jianmu.self_learning.darwinforge.ood_retention_balance import evaluate_guard_candidate


def test_ood_retention_balance_accepts_improving_guard():
    result = evaluate_guard_candidate(None, {"ood_false_accept_before": 0.6, "ood_false_accept_after": 0.4, "arithmetic_supported_retention_before": 1.0, "arithmetic_supported_retention_after": 1.0}, [], [{}])
    assert result["guard_delta_accepted"] is True


def test_ood_retention_balance_rolls_back_supported_regression():
    result = evaluate_guard_candidate(None, {"ood_false_accept_before": 0.6, "ood_false_accept_after": 0.4, "arithmetic_supported_retention_before": 1.0, "arithmetic_supported_retention_after": 0.8}, [], [{}])
    assert result["guard_delta_accepted"] is False
    assert result["rollback_reason"] == "supported_retention_regression"


def test_ood_retention_balance_rolls_back_global_beam_regression():
    result = evaluate_guard_candidate(None, {"ood_false_accept_before": 0.6, "ood_false_accept_after": 0.4, "global_beam_before": 0.5, "global_beam_after": 0.1}, [], [{}])
    assert result["rollback_reason"] == "global_beam_regression"
