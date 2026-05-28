from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def write_state_budget_failure_analysis(output_records: str | Path, rows: List[Dict[str, Any]]) -> None:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    examples = []
    for row in rows:
        if row.get("candidate_miss_rate", 0.0) > 0.0:
            examples.append({
                "profile_name": row["profile_name"],
                "failure_type": "candidate_miss_remaining",
                "candidate_miss_rate": row["candidate_miss_rate"],
                "materialization_level": row["materialization_level"],
            })
    (out / "state_budget_failure_examples.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples[:50]),
        encoding="utf-8",
    )

