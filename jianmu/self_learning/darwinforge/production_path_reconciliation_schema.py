from __future__ import annotations

STILL_NOT_PROVEN = [
    "production function support",
    "production array support",
    "production recursion support",
    "arbitrary project parsing",
    "formal Turing completeness proof",
    "solved program synthesis",
    "production readiness",
    "natural language layer completed",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "emergence proven",
]

EXPERIMENTAL_POLICIES = {
    "canonical_function_targetir": "function",
    "canonical_array_targetir": "array",
    "canonical_function_array_targetir": "function_array",
    "canonical_structured_recursion_targetir": "structured_recursion",
}


def base_claim_flags():
    return {
        "default_profile_unchanged": True,
        "real_promotion_disabled": True,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_official_release": False,
        "still_not_proven": list(STILL_NOT_PROVEN),
    }


def policy_metadata(policy):
    kind = EXPERIMENTAL_POLICIES.get(policy)
    if not kind:
        return {
            "policy": policy,
            "supported": False,
            "experimental_active_path": False,
            "production_supported": False,
        }
    return {
        "policy": policy,
        "kind": kind,
        "supported": True,
        "experimental_active_path": True,
        "production_supported": False,
    }

