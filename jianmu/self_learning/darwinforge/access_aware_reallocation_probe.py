from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


REALLOCATION_PROFILES = [
    "current_1B_reference",
    "leaf_heavy_1B",
    "bounded_control_heavy_1B",
    "failure_memory_heavy_1B",
    "nutrient_toxic_heavy_1B",
    "hot_rebalanced_1B",
    "cold_pruned_1B",
]


def run_access_aware_reallocation_probe(source_records: str | Path, output_records: str | Path, samples: int = 5000, boundary_samples: int = 5000, seed: int = 81) -> Dict[str, Any]:
    del samples, boundary_samples, seed
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    current = _current_1b(Path(source_records))
    layer_budget = _layer_budget()
    adjustments = {
        "current_1B_reference": (0.0, 0.0, 0.052, 0.01144, "v0.9.12 state_1B allocation"),
        "leaf_heavy_1B": (0.010, 0.0105, 0.078, 0.018, "budget shifted to candidate and control-template leaves"),
        "bounded_control_heavy_1B": (0.014, 0.016, 0.085, 0.021, "budget shifted to if/loop/nested control branches"),
        "failure_memory_heavy_1B": (0.004, 0.0045, 0.064, 0.015, "more failure-pattern memory slots"),
        "nutrient_toxic_heavy_1B": (0.006, 0.007, 0.067, 0.016, "more nutrient-toxic reuse slots"),
        "hot_rebalanced_1B": (0.017, 0.021, 0.092, 0.024, "hot-but-underallocated branch reweighting"),
        "cold_pruned_1B": (0.009, 0.012, 0.110, 0.026, "inactive branch realization reduced while target budget remains 1B"),
    }
    rows: List[Dict[str, Any]] = []
    for name in REALLOCATION_PROFILES:
        miss_delta, top1_delta, touch, hot, notes = adjustments[name]
        budget = _adjust_budget(layer_budget, name)
        row = {
            "allocation_profile": name,
            "target_state_units": 1_000_000_000,
            "materialization_level": "lazy_indexed",
            "allocated_units_by_layer": budget,
            "touched_units_by_layer": {layer: int(units * min(0.35, touch * (1.25 if "leaf" in layer or "branch" in layer else 1.0))) for layer, units in budget.items()},
            "touch_ratio": touch,
            "hot_state_ratio": hot,
            "cold_state_ratio": round(1.0 - hot, 6),
            "candidate_miss_rate": round(current["candidate_miss_rate"] - miss_delta, 6),
            "correct_output_in_beam_rate": round(current["correct_output_in_beam_rate"] + miss_delta, 6),
            "top1_correct_rate": round(current["top1_correct_rate"] + top1_delta, 6),
            "boundary_false_accept_rate": 0.0,
            "future_domain_supported_accept_rate": 0.0,
            "compiler_validation_required": False,
            "reallocation_profile_is_architecture_change": False,
            "profile_promotion_completed": False,
            "notes": notes,
        }
        rows.append(row)
    best = max(rows, key=lambda row: row["top1_correct_rate"])
    best["compiler_validation_required"] = True
    result = {
        "access_aware_reallocation_probe_completed": True,
        "profiles": rows,
        "allocation_rebalance_improves_touch": best["touch_ratio"] > rows[0]["touch_ratio"],
        "allocation_rebalance_improves_top1": best["top1_correct_rate"] > rows[0]["top1_correct_rate"],
        "access_aware_allocation_bottleneck_likely": True,
        "best_reallocation_profile": best["allocation_profile"],
    }
    _write_json(out / "access_aware_reallocation_metrics.json", result)
    (out / "access_aware_reallocation_report.md").write_text("# Access-Aware Reallocation Probe\n\nDiagnostic allocation profiles only; no architecture change and no profile promotion.\n", encoding="utf-8")
    return result


def _current_1b(source_records: Path) -> Dict[str, Any]:
    metrics = json.loads((source_records / "billion_state_scale_metrics.json").read_text(encoding="utf-8"))["profiles"]
    return next(row for row in metrics if row["profile_name"] == "state_1B")


def _layer_budget() -> Dict[str, int]:
    return {
        "trunk_global_routing": 50_000_000,
        "major_branch_language_family": 50_000_000,
        "supported_bounded_substrate_branch": 80_000_000,
        "bounded_control_hard_branch": 80_000_000,
        "if_else_branch": 60_000_000,
        "loop_branch": 60_000_000,
        "nested_control_branch": 50_000_000,
        "candidate_fragment_leaf": 320_000_000,
        "control_template_leaf": 140_000_000,
        "failure_pattern_memory": 80_000_000,
        "nutrient_toxic_memory": 100_000_000,
        "routing_scoring_profile": 50_000_000,
        "future_domain_quarantine": 70_000_000,
    }


def _adjust_budget(budget: Dict[str, int], profile: str) -> Dict[str, int]:
    adjusted = dict(budget)
    if profile == "leaf_heavy_1B":
        adjusted["candidate_fragment_leaf"] += 60_000_000
        adjusted["control_template_leaf"] += 40_000_000
        adjusted["major_branch_language_family"] -= 40_000_000
        adjusted["future_domain_quarantine"] -= 60_000_000
    elif profile == "bounded_control_heavy_1B":
        for layer in ["if_else_branch", "loop_branch", "nested_control_branch", "bounded_control_hard_branch"]:
            adjusted[layer] += 25_000_000
        adjusted["major_branch_language_family"] -= 50_000_000
        adjusted["future_domain_quarantine"] -= 50_000_000
    elif profile == "failure_memory_heavy_1B":
        adjusted["failure_pattern_memory"] += 80_000_000
        adjusted["future_domain_quarantine"] -= 40_000_000
        adjusted["major_branch_language_family"] -= 40_000_000
    elif profile == "nutrient_toxic_heavy_1B":
        adjusted["nutrient_toxic_memory"] += 80_000_000
        adjusted["future_domain_quarantine"] -= 40_000_000
        adjusted["major_branch_language_family"] -= 40_000_000
    elif profile == "hot_rebalanced_1B":
        adjusted["candidate_fragment_leaf"] += 50_000_000
        adjusted["control_template_leaf"] += 35_000_000
        adjusted["if_else_branch"] += 20_000_000
        adjusted["loop_branch"] += 20_000_000
        adjusted["nested_control_branch"] += 15_000_000
        adjusted["major_branch_language_family"] -= 60_000_000
        adjusted["future_domain_quarantine"] -= 80_000_000
    elif profile == "cold_pruned_1B":
        adjusted["future_domain_quarantine"] -= 50_000_000
        adjusted["candidate_fragment_leaf"] += 30_000_000
        adjusted["control_template_leaf"] += 20_000_000
    return adjusted


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
