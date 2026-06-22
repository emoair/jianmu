from jianmu.self_learning.darwinforge.redqueen_recovery_annealing_audit import audit_recovery_annealing


def test_recovery_annealing_is_gradual():
    cycles = [
        {"cycle_index": 1, "plan": {"category_weights": {"function": 1.12}}},
        {"cycle_index": 2, "plan": {"category_weights": {"function": 1.2, "mixed": 1.1}}},
        {"cycle_index": 3, "plan": {"category_weights": {"function": 1.13, "mixed": 1.14}}},
        {"cycle_index": 4, "plan": {"category_weights": {"mixed": 1.02}}},
    ]
    result = audit_recovery_annealing(cycles)
    assert result["recovery_annealing_audit_passed"] is True
