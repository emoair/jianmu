from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_turing_frontier_v2_readiness(output_records: str | Path, audit: Dict[str, Any], coverage: Dict[str, Any], compiler_spot: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    scales = audit.get("scales", {})
    result = {
        "dataset_v2_generation_completed": True,
        "dataset_v2_audit_passed": bool(scales) and all(row.get("audit_passed", False) for row in scales.values()),
        "dataset_v2_scales_completed": list(scales.keys()),
        "dataset_v2_total_samples": sum(row.get("total_count", 0) for row in scales.values()),
        "dataset_v2_ready_for_active_generation_loop": coverage.get("dataset_v2_ready_for_active_generation_loop", False),
        "dataset_v2_ready_for_function_array_frontier_probe": coverage.get("dataset_v2_ready_for_function_array_frontier_probe", False),
        "dataset_v2_compiler_spot_clean": compiler_spot.get("backend_claim_safe", False) and compiler_spot.get("future_domain_compiled_count", 0) == 0,
    }
    _write_json(out / "turing_frontier_v2_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
