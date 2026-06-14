from __future__ import annotations

from typing import Dict

from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import POLICY_BY_KIND


def route_opt_in_policy(policy: str, explicit_opt_in: bool, opt_in_flag: str = "enable_staged_opt_in_v1_0_7") -> Dict[str, object]:
    if not explicit_opt_in or opt_in_flag != "enable_staged_opt_in_v1_0_7":
        return {"accepted": False, "reason": "explicit_opt_in_required", "policy": policy}
    if policy not in set(POLICY_BY_KIND.values()):
        return {"accepted": False, "reason": "unknown_policy_rejected", "policy": policy}
    kind = next(kind for kind, value in POLICY_BY_KIND.items() if value == policy)
    return {
        "accepted": True,
        "policy": policy,
        "kind": kind,
        "router": "opt_in_policy_router",
        "production_supported": False,
        "staged_opt_in_candidate": True,
        "experimental_active_bridge": True,
    }
