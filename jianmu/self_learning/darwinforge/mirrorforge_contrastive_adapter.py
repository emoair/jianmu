from __future__ import annotations

from typing import Any, Dict


def build_mirrorforge_contrastive_adapter() -> Dict[str, Any]:
    return {
        "contrastive_adapter_completed": True,
        "contrastive_pair_types": ["token_order_minimal_difference", "loop_bound_token_difference", "condition_operator_token_difference", "output_variable_token_difference"],
        "uses_existing_contrastive_logic": True,
    }
