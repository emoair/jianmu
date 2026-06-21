from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_cycle_metrics(cycle_dir: str | Path, cycle_index: int, metrics: Dict[str, Any], name: str) -> Dict[str, Any]:
    result = {
        "cycle_index": cycle_index,
        "metrics_snapshot_created": True,
        "categories": metrics.get("categories", []),
    }
    path = Path(cycle_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def derive_post_metrics(pre_metrics: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    dist = execution.get("actual_category_distribution", {})
    return {
        "categories": [
            {
                **item,
                "category_event_count": dist.get(item["category"], 0),
                "actual_review_count": int(round(dist.get(item["category"], 0) * float(execution.get("actual_review_allocation", {}).get(item["category"], 1.0)))),
                "actual_difficulty_mean": execution.get("actual_difficulty_distribution", {}).get(item["category"], 1),
                "actual_review_weight": execution.get("actual_review_allocation", {}).get(item["category"], 1.0),
                "actual_shape_diversity_count": dist.get(item["category"], 0) if item.get("coverage_gap", 0.0) > 0 else 0,
                "actual_boundary_recheck_count": dist.get(item["category"], 0) if item["category"] in {"default_blocking", "unsupported_boundary"} else 0,
                "actual_rollback_recheck_count": execution.get("actual_category_distribution", {}).get("rollback", 0) if item["category"] == "mixed" else 0,
                "actual_replay_recheck_count": execution.get("actual_category_distribution", {}).get("replay", 0) if item["category"] == "mixed" else 0,
            }
            for item in pre_metrics.get("categories", [])
        ]
    }
