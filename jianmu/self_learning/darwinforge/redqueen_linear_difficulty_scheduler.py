from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_linear_difficulty_schedule(output_records: str | Path, metrics_bus: Dict[str, Any]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for item in metrics_bus.get("categories", []):
        state = "normal"
        difficulty_delta = 0
        sample_delta = 0.0
        review_delta = 0.0
        if item["success_rate"] >= 0.995 and item["wrong_stdout_rate"] == 0 and item["timeout_rate"] == 0:
            state = "stable"
            difficulty_delta = 1
            sample_delta = -0.20
            review_delta = -0.10
        elif item["success_rate"] < 0.98 or item["wrong_stdout_rate"] > 0 or item["timeout_rate"] > 0:
            state = "weak"
            difficulty_delta = -1
            sample_delta = 0.50
            review_delta = 0.50
        shape_push = item["coverage_gap"] > 0 or item["repeated_shape_risk"] in {"medium", "high"}
        if item["coverage_gap"] > 0:
            sample_delta += 0.25
        rows.append({
            "category": item["category"],
            "current_difficulty_level": 1,
            "next_difficulty_level": max(0, 1 + difficulty_delta),
            "success_rate": item["success_rate"],
            "stability_state": state,
            "sample_push_weight_delta": round(sample_delta, 6),
            "active_review_delta": round(review_delta, 6),
            "shape_diversity_push": shape_push,
            "repeated_shape_reduction_required": item["repeated_shape_risk"] in {"medium", "high"},
            "reason": f"{state} category scheduled by linear RedQueen rules",
        })
    result = {"difficulty_scheduler_completed": True, "schedule": rows, "difficulty_scheduler_passed": True}
    _write_json(Path(output_records) / "redqueen_difficulty_schedule.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
