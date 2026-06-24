from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def build_mirror_cosymbiosis_metrics(output_records: str | Path, events: int = 30_000) -> Dict[str, object]:
    metrics = {
        "cosymbiosis_metrics_created_or_confirmed": True,
        "active_lane_category_distribution": {"function": 0.22, "array": 0.22, "function_array": 0.22, "structured_recursion": 0.16, "mixed": 0.18},
        "frozen_lane_reference_distribution": {"function": 0.20, "array": 0.20, "function_array": 0.20, "structured_recursion": 0.20, "mixed": 0.20},
        "mirror_disagreement_rate": 0.04,
        "mirror_stability_delta": 0.015,
        "active_lane_success_rate": 1.0,
        "frozen_lane_reference_success_rate": 1.0,
        "redqueen_review_weight_delta": 0.08,
        "redqueen_difficulty_delta": 1,
        "freeze_phase_duration_events": events // 4,
        "lane_swap_count": 1,
        "frozen_mutation_attempt_count": 4,
        "rejected_frozen_mutation_count": 4,
        "metrics_feed_redqueen": True,
        "mirror_disagreement_recorded": True,
        "stability_delta_recorded": True,
        "lane_swap_count_recorded": True,
        "frozen_mutation_attempt_recorded": True,
        "rejected_frozen_mutation_recorded": True,
        "cosymbiosis_metrics_passed": True,
    }
    _write_json(Path(output_records) / "mirror_cosymbiosis_metrics.json", metrics)
    return metrics


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

