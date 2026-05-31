from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_v0_9_18_resume_manifest(source_records: str | Path) -> Dict[str, Any]:
    root = Path(source_records)
    scale_path = root / "ironjudge_scale_validation.json"
    manifest_path = root / "ironjudge_trace_manifest.json"
    if not scale_path.exists() or not manifest_path.exists():
        return {"resume_from_v0_9_18": False, "missing_source_records": True, "previous_traces": []}
    scale = json.loads(scale_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    traces: List[Dict[str, Any]] = []
    for shard in manifest.get("shards", []):
        path = root / shard["path"]
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        traces.append(json.loads(line))
    valid = [row for row in traces if row.get("compiler_invoked") and row.get("compiler_verified_correct")]
    invalid = [row for row in traces if row.get("compiler_invoked") and not row.get("compiler_verified_correct")]
    return {
        "resume_from_v0_9_18": True,
        "missing_source_records": False,
        "scale_validation": scale,
        "trace_manifest": manifest,
        "previous_traces": traces,
        "previous_valid_traces": valid,
        "previous_invalid_traces": invalid,
        "completed_sample_hashes": sorted({str(row.get("sample_id_hash")) for row in valid}),
    }
