from __future__ import annotations

from typing import Dict

from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import POLICY_BY_KIND


def route_dry_run_policy(policy: str) -> Dict[str, object]:
    if policy not in set(POLICY_BY_KIND.values()):
        return {"accepted": False, "reason": "unknown_policy_rejected", "policy": policy}
    kind = next(kind for kind, value in POLICY_BY_KIND.items() if value == policy)
    return {
        "accepted": True,
        "policy": policy,
        "kind": kind,
        "router": "dry_run_policy_router",
        "production_supported": False,
        "dry_run_enabled": True,
        "experimental_active_bridge": True,
    }
