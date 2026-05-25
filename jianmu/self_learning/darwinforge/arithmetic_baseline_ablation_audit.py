from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

METHODS = ["full_jianmu", "random_router", "heuristic_router", "no_root_colony", "no_nutrient_toxic_memory", "no_lifecycle_state"]


def audit_baseline_ablation(records_dir: str | Path, output_dir: str | Path) -> Dict[str, Any]:
    records = Path(records_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    full_metrics = _load_json(records / "arithmetic_training_metrics.json")
    rows: List[Dict[str, Any]] = []
    for method in METHODS:
        if method == "full_jianmu":
            rows.append({
                "method": method,
                "executed": True,
                "actual_sample_count": full_metrics.get("actual_eval_iterated_count", 0) + full_metrics.get("actual_heldout_iterated_count", 0),
                "supported_success_rate": full_metrics.get("heldout_supported_success_rate"),
                "boundary_false_accept_rate": max(
                    full_metrics.get("unsupported_false_accept_rate", 1.0),
                    full_metrics.get("trap_false_accept_rate", 1.0),
                    full_metrics.get("future_domain_supported_accept_rate", 1.0),
                    full_metrics.get("near_ood_supported_accept_rate", 1.0),
                ),
                "delta_vs_full": 0.0,
                "metric_computed_from_samples": False,
                "fixed_summary_detected": True,
                "notes": "Full v0.9.3 aggregate exists, but no baseline per-sample audit trace is present.",
            })
        else:
            rows.append({
                "method": method,
                "executed": False,
                "actual_sample_count": 0,
                "supported_success_rate": "missing",
                "boundary_false_accept_rate": "missing",
                "delta_vs_full": "missing",
                "metric_computed_from_samples": False,
                "fixed_summary_detected": False,
                "notes": "Missing in v0.9.3 records; not fabricated by v0.9.3.1.",
            })
    payload = {
        "baseline_ablation_audit_passed": False,
        "baseline_gap_verified": False,
        "methods": rows,
        "notes": "v0.9.3 did not include real baseline/ablation arithmetic audit records.",
    }
    _write_json(out / "baseline_ablation_audit.json", payload)
    (out / "baseline_ablation_audit.md").write_text(_md(payload), encoding="utf-8")
    return payload


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _md(payload: Dict[str, Any]) -> str:
    lines = ["# v0.9.3 Baseline / Ablation Audit", "", f"- baseline_gap_verified: {payload['baseline_gap_verified']}", ""]
    for row in payload["methods"]:
        lines.append(f"- {row['method']}: executed={row['executed']}, notes={row['notes']}")
    return "\n".join(lines) + "\n"
