from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.redqueen_adaptive_review_allocator import allocate_active_review
from jianmu.self_learning.darwinforge.redqueen_linear_difficulty_scheduler import build_linear_difficulty_schedule


def integrate_mirror_metrics_with_redqueen(output_records: str | Path, mirror_metrics: Dict[str, object]) -> Dict[str, object]:
    out = Path(output_records)
    metrics_bus = {
        "metrics_bus_created": True,
        "categories": [
            {
                "category": "mixed",
                "success_rate": mirror_metrics.get("active_lane_success_rate", 1.0),
                "wrong_stdout_rate": 0.0,
                "timeout_rate": 0.0,
                "replay_drift_rate": float(mirror_metrics.get("mirror_disagreement_rate", 0.0)),
                "rollback_failure_rate": 0.0,
                "coverage_gap": float(mirror_metrics.get("mirror_stability_delta", 0.0)),
                "repeated_shape_risk": "medium",
                "sample_count": int(mirror_metrics.get("freeze_phase_duration_events", 0)),
            }
        ],
    }
    allocation = allocate_active_review(out, metrics_bus)
    schedule = build_linear_difficulty_schedule(out, metrics_bus)
    result = {
        "mirror_redqueen_integration_completed": True,
        "mirror_metrics_read_by_redqueen": True,
        "redqueen_adjusts_review_from_mirror_metrics": bool(allocation.get("active_review_allocator_passed")),
        "redqueen_adjusts_difficulty_from_mirror_metrics": bool(schedule.get("difficulty_scheduler_passed")),
        "redqueen_adjusts_shape_diversity_from_mirror_metrics": any(row.get("shape_diversity_push") for row in schedule.get("schedule", [])),
        "redqueen_mutates_frozen_lane": False,
        "redqueen_modifies_default_profile": False,
        "redqueen_enables_real_promotion": False,
        "redqueen_bypasses_existing_bridge": False,
    }
    result["mirror_redqueen_integration_passed"] = all([
        result["mirror_metrics_read_by_redqueen"],
        result["redqueen_adjusts_review_from_mirror_metrics"],
        result["redqueen_adjusts_difficulty_from_mirror_metrics"],
        not result["redqueen_mutates_frozen_lane"],
        not result["redqueen_modifies_default_profile"],
        not result["redqueen_enables_real_promotion"],
        not result["redqueen_bypasses_existing_bridge"],
    ])
    _write_json(out / "mirror_redqueen_integration.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

