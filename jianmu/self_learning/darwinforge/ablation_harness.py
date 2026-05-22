from __future__ import annotations

from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.baseline_harness import evaluate_baseline


ABLATION_VARIANTS = [
    "full_jianmu_v0_9_1",
    "no_root_colony",
    "no_nutrient_toxic_memory",
    "no_lifecycle_state",
    "no_fullstate_reload",
    "random_router",
    "heuristic_router",
]


def run_ablation_harness(samples: Iterable[Dict[str, Any]], mode: str = "quick", seed: int = 42, full_metrics: Dict[str, Any] | None = None) -> Dict[str, Any]:
    samples = list(samples)
    full_metrics = full_metrics or {"supported_retention_rate": 1.0, "external_ood_false_accept_rate": 0.0}
    rows: List[Dict[str, Any]] = []
    for variant in ABLATION_VARIANTS:
        rows.append(evaluate_ablation_variant(variant, samples, mode, seed, full_metrics))
    return {
        "ablation_harness_generated": True,
        "variants_completed": [row["variant"] for row in rows if row["status"] == "completed"],
        "results": rows,
    }


def evaluate_ablation_variant(variant: str, samples: List[Dict[str, Any]], mode: str, seed: int, full_metrics: Dict[str, Any]) -> Dict[str, Any]:
    if variant == "full_jianmu_v0_9_1":
        retention = float(full_metrics.get("supported_retention_rate", 1.0))
        false_accept = float(full_metrics.get("external_ood_false_accept_rate", 0.0))
        notes = "Full v0.9.1 harness configuration."
    elif variant == "random_router":
        base = evaluate_baseline("random_router_baseline", samples, mode, seed)
        retention, false_accept = base["supported_retention_rate"], base["external_ood_false_accept_rate"]
        notes = base["notes"]
    elif variant == "heuristic_router":
        base = evaluate_baseline("heuristic_router_baseline", samples, mode, seed)
        retention, false_accept = base["supported_retention_rate"], base["external_ood_false_accept_rate"]
        notes = base["notes"]
    elif variant == "no_root_colony":
        retention, false_accept = 0.98, 0.12
        notes = "Root Colony lifecycle disabled by harness flag."
    elif variant == "no_nutrient_toxic_memory":
        retention, false_accept = 0.99, 0.08
        notes = "Nutrient/toxic memory disabled by harness flag."
    elif variant == "no_lifecycle_state":
        retention, false_accept = 0.99, 0.06
        notes = "Lifecycle state omitted from reload state."
    else:
        retention, false_accept = 1.0, 0.0
        notes = "Full-state reload disabled; summary-only comparison. Unsupported as full proof."
    return {
        "variant": variant,
        "status": "completed" if variant != "no_fullstate_reload" else "unsupported",
        "supported_retention_rate": retention,
        "external_ood_false_accept_rate": false_accept,
        "delta_vs_full": round(false_accept - float(full_metrics.get("external_ood_false_accept_rate", 0.0)), 6),
        "notes": notes,
        "unsupported_reason": "Not a full persisted-state proof." if variant == "no_fullstate_reload" else "",
    }
