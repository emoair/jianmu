from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def summarize_turing_frontier_v2_coverage(dataset_dir: str | Path, output_records: str | Path) -> Dict[str, Any]:
    root = Path(dataset_dir)
    scales: Dict[str, Any] = {}
    missing = []
    for scale_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        audit_path = scale_dir / "audit.json"
        coverage_path = scale_dir / "coverage_map.json"
        if not audit_path.exists() or not coverage_path.exists():
            missing.append(scale_dir.name)
            continue
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        scales[scale_dir.name] = {"audit": audit, "coverage": coverage}
    result = {
        "dataset_v2_coverage_completed": not missing,
        "scales": scales,
        "dataset_v2_ready_for_active_generation_loop": not missing and all(row["audit"]["audit_passed"] for row in scales.values()),
        "dataset_v2_ready_for_function_array_frontier_probe": not missing and all(row["audit"]["function_frontier_coverage_score"] >= 1.0 and row["audit"]["array_frontier_coverage_score"] >= 1.0 for row in scales.values()),
        "missing_coverage_areas": missing,
        "overrepresented_areas": [],
        "recommended_next_dataset_actions": ["active data generation loop dry-run", "function/array frontier probe with future-domain isolation"],
    }
    out = Path(output_records)
    _write_json(out / "dataset_v2_coverage_summary.json", result)
    (out / "dataset_v2_coverage_summary.md").write_text("# Dataset v2 Coverage Summary\n\nTuring-frontier v2 coverage is a data-grounding audit, not a Turing-completeness claim.\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
