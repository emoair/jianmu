from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_governance_schema import RedQueenAllocatorConfig


def allocate_active_review(output_records: str | Path, metrics_bus: Dict[str, Any], config: RedQueenAllocatorConfig | None = None) -> Dict[str, Any]:
    cfg = config or RedQueenAllocatorConfig()
    risk_scores: Dict[str, float] = {}
    weights: Dict[str, float] = {}
    reasoning: Dict[str, str] = {}
    for item in metrics_bus.get("categories", []):
        cat = item["category"]
        risk = (
            0.45 * (1 - item["success_rate"])
            + 0.20 * item["wrong_stdout_rate"]
            + 0.15 * item["timeout_rate"]
            + 0.10 * item["replay_drift_rate"]
            + 0.05 * item["rollback_failure_rate"]
            + 0.05 * item["coverage_gap"]
        )
        if cat in {"default_blocking", "unsupported_boundary"}:
            risk = max(risk, 0.05)
        weight = max(cfg.min_weight, min(cfg.max_weight, cfg.base_weight + cfg.alpha * risk))
        risk_scores[cat] = round(risk, 6)
        weights[cat] = round(weight, 6)
        reasoning[cat] = f"risk={risk_scores[cat]} from success/timeout/stdout/replay/coverage metrics"
    highest = max(risk_scores, key=risk_scores.get)
    lowest = min(risk_scores, key=risk_scores.get)
    result = {
        "active_review_allocator_completed": True,
        "category_risk_scores": risk_scores,
        "category_review_weights": weights,
        "highest_risk_category": highest,
        "lowest_risk_category": lowest,
        "allocation_reasoning": reasoning,
        "active_review_allocator_passed": all(weight > 0 for weight in weights.values()),
    }
    _write_json(Path(output_records) / "redqueen_active_review_allocation.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
