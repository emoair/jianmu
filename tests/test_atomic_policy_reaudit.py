from jianmu.self_learning.darwinforge.atomic_policy_reaudit import reaudit_atomic_policies


def test_atomic_policy_reaudit_confirms_all_new_policies():
    result = reaudit_atomic_policies()
    assert result["atomic_policy_bridge_confirmed"] is True
    assert all(result["accepted"].values())
    assert result["unknown_policy_rejected"] is True
    assert result["arithmetic_regression_path_confirmed"] is True

