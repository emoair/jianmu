from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


def write_iteration_trace(output_records: str | Path, rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    path = Path(output_records) / "redqueen_iteration_trace.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return {
        "iteration_trace_generated": True,
        "iteration_trace_path": str(path),
        "iteration_trace_events": count,
    }
