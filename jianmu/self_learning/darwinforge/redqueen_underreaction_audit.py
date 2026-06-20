from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_overreaction_audit import audit_overreaction


def audit_over_under_reaction(output_records: str | Path, pre_metrics: Dict[str, Any], post_metrics: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    over = audit_overreaction(pre_metrics, post_metrics, execution)
    actual_review = execution.get("actual_review_allocation", {})
    actual_dist = execution.get("actual_category_distribution", {})
    weak_not_boosted = 0
    replay_ignored = 0
    rollback_ignored = 0
    shape_ignored = 0
    for item in pre_metrics.get("categories", []):
        category = item["category"]
        weak = item["success_rate"] < 0.98 or item["wrong_stdout_rate"] > 0 or item["timeout_rate"] > 0
        if weak and actual_review.get(category, 1.0) <= item.get("review_weight", 1.0):
            weak_not_boosted += 1
        if item.get("coverage_gap", 0.0) > 0 and actual_dist.get(category, 0) == 0:
            shape_ignored += 1
        if item.get("replay_drift_rate", 0.0) > 0 and actual_dist.get("replay", 0) == 0:
            replay_ignored += 1
        if item.get("rollback_failure_rate", 0.0) > 0 and actual_dist.get("rollback", 0) == 0:
            rollback_ignored += 1
    underreaction = any([weak_not_boosted, replay_ignored, rollback_ignored, shape_ignored])
    result = {
        **over,
        "underreaction_audit_completed": True,
        "underreaction_detected": underreaction,
        "weak_category_not_boosted_count": weak_not_boosted,
        "coverage_gap_shape_diversity_ignored_count": shape_ignored,
        "replay_recheck_ignored_count": replay_ignored,
        "rollback_recheck_ignored_count": rollback_ignored,
    }
    result["over_under_reaction_audit_passed"] = all([
        not result["overreaction_detected"],
        not result["underreaction_detected"],
        result["boundary_review_zeroed_count"] == 0,
    ])
    _write_json(Path(output_records) / "redqueen_over_under_reaction_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
