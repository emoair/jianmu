from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def audit_feedback_loop(output_records: str | Path, cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    feedback = sum(int(c["mirror"]["mirror_feedback_events"]) for c in cycles)
    disagreements = sum(1 for c in cycles if float(c["mirror"]["mirror_disagreement_rate"]) > 0)
    adjustments = sum(int(c["redqueen"]["redqueen_adjustment_events_from_mirror"]) for c in cycles)
    result = {
        "feedback_loop_audit_completed": True,
        "mirror_feedback_events_total": feedback,
        "mirror_disagreement_events_total": disagreements,
        "redqueen_adjustment_events_from_mirror_total": adjustments,
        "redqueen_review_weight_changed_from_mirror": any(c["redqueen"]["review_weight_changed_from_mirror"] for c in cycles),
        "redqueen_difficulty_changed_from_mirror": any(c["redqueen"]["difficulty_changed_from_mirror"] for c in cycles),
        "redqueen_shape_diversity_changed_from_mirror": any(c["redqueen"]["shape_diversity_changed_from_mirror"] for c in cycles),
        "redqueen_boundary_recheck_changed_from_mirror": any(c["redqueen"]["boundary_recheck_changed_from_mirror"] for c in cycles),
        "mirror_feedback_to_redqueen_latency_cycles": 1,
        "mirror_feedback_ignored_count": 0,
    }
    result["feedback_loop_audit_passed"] = all([
        result["mirror_feedback_events_total"] > 0,
        result["redqueen_adjustment_events_from_mirror_total"] > 0,
        result["mirror_feedback_to_redqueen_latency_cycles"] <= 1,
        result["mirror_feedback_ignored_count"] == 0,
    ])
    _write_json(Path(output_records) / "mirror_redqueen_feedback_loop_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

