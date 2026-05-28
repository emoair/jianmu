from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def write_billion_state_failure_analysis(output_records: str | Path, metrics: List[Dict[str, Any]], access: Dict[str, Any]) -> None:
    access_rows = {row["profile_name"]: row for row in access.get("profiles", [])}
    examples = []
    for row in metrics:
        examples.append({
            "profile_name": row["profile_name"],
            "failure_type": "candidate_miss_remaining",
            "candidate_miss_rate": row["candidate_miss_rate"],
            "touch_ratio": access_rows.get(row["profile_name"], {}).get("touch_ratio", 0.0),
        })
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "billion_state_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples[:50]), encoding="utf-8")

