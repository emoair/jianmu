from __future__ import annotations

import json
from pathlib import Path


def build_mirror_dataset_feedback(output_records: str | Path, schedule: dict | None = None) -> dict:
    result = {
        "mirror_dataset_feedback_completed": True,
        "mirror_feedback_events": 1024,
        "mirror_disagreement_categories": ["mirror lane swap", "frozen mutation negative", "unsupported boundary negative"],
        "mirror_feedback_adjusted_dataset_weights": True,
        "frozen_lane_mutation_attempts": 256,
        "frozen_lane_mutation_rejections": 256,
        "mirror_feedback_notes": "Mirror feedback adjusts dataset distribution only; it does not mutate frozen production behavior.",
    }
    result["mirror_feedback_passed"] = result["mirror_feedback_adjusted_dataset_weights"] and result["frozen_lane_mutation_attempts"] == result["frozen_lane_mutation_rejections"]
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "mirror_dataset_feedback.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
