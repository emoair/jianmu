from jianmu.self_learning.darwinforge.dry_run_policy_router import route_dry_run_policy


def test_dry_run_policy_router_rejects_unknown_policy():
    result = route_dry_run_policy("unknown_policy")
    assert result["accepted"] is False
    assert result["reason"] == "unknown_policy_rejected"
