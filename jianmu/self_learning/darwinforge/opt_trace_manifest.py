from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable


def build_opt_trace_manifest(output_records: str | Path, snapshots: Iterable[Dict[str, object]]) -> Path:
    path = Path(output_records) / "opt_trace_manifest.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in snapshots:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path

