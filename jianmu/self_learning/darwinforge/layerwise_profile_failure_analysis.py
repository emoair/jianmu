from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_layerwise_profile_failure_analysis(output_records: str | Path, gates: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    failures = []
    for key, value in gates.items():
        if key.endswith("_gate") and isinstance(value, dict) and not value.get("passed", True):
            failures.append({"gate": key, "failure_reason": value.get("failure_reason"), "severity": value.get("severity"), "metric_values": value.get("metric_values")})
    result = {"failure_analysis_completed": True, "failure_count": len(failures), "failures": failures}
    (out / "profile_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in failures), encoding="utf-8")
    return result
