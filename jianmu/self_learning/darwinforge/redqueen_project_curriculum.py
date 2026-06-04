from __future__ import annotations

from typing import Dict


def build_redqueen_project_curriculum() -> Dict[str, object]:
    return {
        "targeted_project_curriculum_enabled": True,
        "assignments": ["call_graph_variation", "array_loop_interop", "counter_machine_witness", "heldout_names"],
        "real_promotion_enabled": False,
    }

