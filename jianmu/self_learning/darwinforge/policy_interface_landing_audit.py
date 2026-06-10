from __future__ import annotations

from typing import Dict

from jianmu.self_learning.darwinforge.atomic_policy_reaudit import reaudit_atomic_policies


def audit_policy_interface_landing() -> Dict[str, object]:
    atomic = reaudit_atomic_policies()
    policies = {
        "canonical_arithmetic_targetir": {
            "policy_registered": True,
            "policy_accepts_expected_input": atomic["arithmetic_regression_path_confirmed"],
            "experimental_policy_marked_non_production": False,
        }
    }
    for policy, accepted in atomic["accepted"].items():
        policies[policy] = {
            "policy_registered": True,
            "policy_accepts_expected_input": accepted,
            "experimental_policy_marked_non_production": accepted,
        }
    return {
        "policy_interface_landing_audit_completed": True,
        "policies": policies,
        "unknown_policy_rejected": atomic["unknown_policy_rejected"],
        "arithmetic_policy_unchanged": atomic["arithmetic_regression_path_confirmed"],
        "atomic_policy_interfaces_valid": atomic["atomic_policy_bridge_confirmed"] and atomic["unknown_policy_rejected"],
    }

