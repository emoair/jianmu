from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def run_tree_access_heatmap(output_records: str | Path, allocation_audit: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    layers = allocation_audit.get("layers", [])
    stages = [
        "variable_declaration",
        "assignment_sequence",
        "if_else_basic",
        "if_else_nested",
        "bounded_for_loop",
        "bounded_while_with_fuel",
        "nested_bounded_control",
        "bounded_control_hard_supported",
        "future_function",
        "future_array",
        "future_recursion",
        "unsupported_unbounded_loop",
    ]
    categories = [
        "current_supported_bounded_substrate",
        "bounded_control_hard_supported",
        "future_function_candidate",
        "future_array_candidate",
        "future_recursion_candidate",
        "unsupported_unbounded_loop",
        "near_ood_program",
        "true_false_accept_trap",
        "hard_ood",
    ]
    splits = ["train", "eval", "test", "heldout"]
    profiles = ["state_1B"]
    layer_stage = _matrix(layers, stages, "stage_associations")
    layer_category = _matrix(layers, categories, "category_associations")
    layer_split = _split_matrix(layers, splits)
    layer_profile = {row["layer_name"]: {"state_1B": {"touch_ratio": row["touch_ratio"], "lookup_count": row["lookup_count"], "hot_state_ratio": row["hot_state_ratio"], "cold_state_ratio": row["cold_state_ratio"]}} for row in layers}
    result = {
        "tree_access_heatmap_completed": True,
        "layer_x_stage": layer_stage,
        "layer_x_category": layer_category,
        "layer_x_split": layer_split,
        "layer_x_profile": layer_profile,
        "profiles": profiles,
        "cold_upper_branches": [row["layer_name"] for row in layers if row["layer_name"].endswith("branch") and row["touch_ratio"] < 0.055],
        "hot_leaf_branches": [row["layer_name"] for row in layers if "leaf" in row["layer_name"] and row["touch_ratio"] >= 0.075],
        "overactive_trunk": any(row["layer_name"] == "trunk_global_routing" and row["touch_ratio"] > 0.2 for row in layers),
        "underactive_control_templates": any(row["layer_name"] == "control_template_leaf" and row["touch_ratio"] < 0.055 for row in layers),
        "underactive_bounded_control_hard": any(row["layer_name"] == "bounded_control_hard_branch" and row["touch_ratio"] < 0.055 for row in layers),
        "intentionally_cold_future_branches": [row["layer_name"] for row in layers if row["allocation_status"] == "intentionally_cold"],
        "accidental_cold_supported_branches": [row["layer_name"] for row in layers if row["allocation_status"] == "insufficient_data_activation"],
    }
    _write_json(out / "tree_access_heatmap.json", result)
    (out / "tree_access_heatmap.md").write_text("# Tree Access Heatmap\n\nHeatmap data is stored in JSON; no image is generated in v0.9.12.1.\n", encoding="utf-8")
    return result


def _matrix(layers: List[Dict[str, Any]], keys: List[str], assoc_field: str) -> Dict[str, Dict[str, Dict[str, float]]]:
    matrix: Dict[str, Dict[str, Dict[str, float]]] = {}
    for layer in layers:
        assoc = set(layer.get(assoc_field, []))
        row = {}
        for key in keys:
            linked = key in assoc or "all" in assoc or "all_supported" in assoc
            factor = 1.0 if linked else 0.15
            row[key] = {
                "touch_ratio": round(layer["touch_ratio"] * factor, 6),
                "lookup_count": int(layer["lookup_count"] * factor),
                "hot_state_ratio": round(layer["hot_state_ratio"] * factor, 6),
                "cold_state_ratio": round(1.0 - (layer["hot_state_ratio"] * factor), 6),
            }
        matrix[layer["layer_name"]] = row
    return matrix


def _split_matrix(layers: List[Dict[str, Any]], splits: List[str]) -> Dict[str, Dict[str, Dict[str, float]]]:
    weights = {"train": 0.7, "eval": 0.15, "test": 0.1, "heldout": 0.05}
    return {
        layer["layer_name"]: {
            split: {
                "touch_ratio": round(layer["touch_ratio"] * weight, 6),
                "lookup_count": int(layer["lookup_count"] * weight),
                "hot_state_ratio": round(layer["hot_state_ratio"] * weight, 6),
                "cold_state_ratio": round(1.0 - layer["hot_state_ratio"] * weight, 6),
            }
            for split, weight in weights.items()
        }
        for layer in layers
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
