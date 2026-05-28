from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


LAYERWISE_LAYERS = [
    "trunk_global_routing",
    "major_branch_language_family",
    "supported_bounded_substrate_branch",
    "bounded_control_hard_branch",
    "if_else_branch",
    "loop_branch",
    "nested_control_branch",
    "candidate_fragment_leaf",
    "control_template_leaf",
    "failure_pattern_memory",
    "nutrient_toxic_memory",
    "routing_scoring_profile",
]

DIAGNOSTIC_PROFILES = [
    "current_1B_reference",
    "hot_rebalanced_1B_reference",
    "branch_activation_balanced_reference",
    "combined_hot_rebalanced_balanced_sampling_1B",
    "layerwise_sparse_1B_freeze_prune",
]


def build_adaptive_layerwise_profiles(names: Iterable[str] | None = None) -> List[Dict[str, Any]]:
    selected = list(names) if names else DIAGNOSTIC_PROFILES
    return [_profile(name) for name in selected]


def write_adaptive_layerwise_profiles(output_records: str | Path, profiles: List[Dict[str, Any]]) -> None:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "adaptive_layerwise_profiles.json").write_text(json.dumps({"profiles": profiles}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _profile(name: str) -> Dict[str, Any]:
    if name not in DIAGNOSTIC_PROFILES:
        raise ValueError(f"unknown adaptive layerwise profile: {name}")
    layerwise = name == "layerwise_sparse_1B_freeze_prune"
    combined = name == "combined_hot_rebalanced_balanced_sampling_1B"
    allocation = "hot_rebalanced_1B" if name in {"hot_rebalanced_1B_reference", "combined_hot_rebalanced_balanced_sampling_1B"} else "current_1B"
    if layerwise:
        allocation = "layerwise_sparse_1B_freeze_prune"
    sampling = "branch_activation_balanced" if name in {"branch_activation_balanced_reference", "combined_hot_rebalanced_balanced_sampling_1B", "layerwise_sparse_1B_freeze_prune"} else "original_sampling_reference"
    return {
        "profile_name": name,
        "allocation_profile": allocation,
        "sampling_profile": sampling,
        "source": "v0.9.12.1 diagnostic result" if name != "current_1B_reference" else "v0.9.12 state_1B",
        "target_state_units_total_logical": 1_000_000_000 * (len(LAYERWISE_LAYERS) if layerwise else 1),
        "target_state_units_per_layer": 1_000_000_000 if layerwise else None,
        "active_state_units_total": 0,
        "materialization_level": "lazy_indexed",
        "layerwise_enabled": layerwise,
        "freeze_prune_enabled": layerwise,
        "combined_profile": combined,
        "profile_is_architecture_change": False,
        "profile_is_layerwise_diagnostic": layerwise,
        "profile_promotion_completed": False,
        "default_profile_promotion": False,
        "layers": LAYERWISE_LAYERS if layerwise else [],
    }
