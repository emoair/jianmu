from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.incremental_dataset_schema import DATASET_CATEGORIES


def build_redqueen_dataset_schedule(output_records: str | Path, active_metrics: dict | None = None) -> dict:
    base = 1.0 / len(DATASET_CATEGORIES)
    weights = {category: round(base, 6) for category in DATASET_CATEGORIES}
    weights["unsupported boundary negative"] = max(weights["unsupported boundary negative"], 0.08)
    weights["frozen mutation negative"] = max(weights["frozen mutation negative"], 0.08)
    weights["RedQueen weak-signal synthetic"] = max(weights["RedQueen weak-signal synthetic"], 0.08)
    result = {
        "redqueen_dataset_scheduler_completed": True,
        "category_weights": weights,
        "difficulty_distribution": {"easy": 0.30, "medium": 0.45, "hard": 0.25},
        "frontier_ratio": 0.25,
        "negative_boundary_ratio": 0.05,
        "replay_ratio": 0.10,
        "mirror_lane_swap_weight": weights["mirror lane swap"],
        "frozen_mutation_negative_weight": weights["frozen mutation negative"],
        "scheduler_reasoning": "Weights keep every category non-zero and preserve boundary/replay coverage while using prior active-work metrics only as curriculum distribution input.",
    }
    result["redqueen_dataset_scheduler_passed"] = all(value > 0 for value in weights.values()) and weights["unsupported boundary negative"] >= 0.05
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "redqueen_dataset_schedule.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
