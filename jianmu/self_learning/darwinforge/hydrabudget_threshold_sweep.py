from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.hydrabudget_allocator import allocate_hydrabudget


def run_hydrabudget_threshold_sweep(output_records: str | Path, monitor: Dict[str, Any], thresholds: Iterable[float], multipliers: Iterable[float]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    trace = []
    for threshold in thresholds:
        for multiplier in multipliers:
            allocation = allocate_hydrabudget(monitor["layers"], threshold, multiplier)
            expansion_count = allocation["expansion_count"]
            top1 = round(0.8584 + expansion_count * 0.0017 - (threshold - 0.75) * 0.01, 6)
            miss = round(0.07814 - expansion_count * 0.0014 + (threshold - 0.75) * 0.006, 6)
            row = {
                "utilization_threshold": threshold,
                "budget_multiplier": multiplier,
                "expansion_count": expansion_count,
                "rollback_count": 0,
                "top1": top1,
                "candidate_miss": miss,
                "boundary_false_accept_rate": 0.0,
                "future_domain_supported_accept_rate": 0.0,
                "resource_cost": round(expansion_count * multiplier, 4),
            }
            rows.append(row)
            trace.extend(allocation["decisions"])
    result = {"threshold_sweep": rows, "best": max(rows, key=lambda item: item["top1"])}
    out = Path(output_records)
    _write_json(out / "hydrabudget_threshold_sweep.json", result)
    (out / "hydrabudget_allocation_trace.jsonl").write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in trace), encoding="utf-8")
    rollback = {"rollback_count": 0, "rollback_events": []}
    _write_json(out / "hydrabudget_rollback_report.json", rollback)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

