from jianmu.self_learning.darwinforge.opt_in_policy_router import route_opt_in_policy


def test_opt_in_policy_router_requires_explicit_flag():
    result = route_opt_in_policy("canonical_function_targetir", explicit_opt_in=False)
    assert result["accepted"] is False
    assert result["reason"] == "explicit_opt_in_required"
