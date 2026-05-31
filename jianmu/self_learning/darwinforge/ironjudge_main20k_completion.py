from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_main20k_completion_not_needed(output_records: str | Path, reconciliation: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "main20k_completion_rerun_executed": False,
        "reason": "main_20k completed clean under cumulative accounting semantics",
        "target_main_invocations": 20000,
        "main_20k_effective_invocations": reconciliation["main_20k_effective_invocations"],
        "new_invocation_count_v0_9_18_2": 0,
        "completed": True,
        "partial": False,
    }
    out = Path(output_records)
    _write_json(out / "main20k_completion_metrics.json", result)
    _write_json(out / "main20k_completion_trace_manifest.json", {"shards": [], "total_rows": 0, "rerun_executed": False})
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
