from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_targeted_failure_analysis(output_records: str | Path, taxonomy: Dict[str, Any], examples: list[Dict[str, Any]]) -> None:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "targeted_candidate_error_taxonomy.json").write_text(
        json.dumps(taxonomy, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "targeted_candidate_examples.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples),
        encoding="utf-8",
    )
    (out / "targeted_failure_analysis.md").write_text(
        "# v0.9.10 Targeted Failure Analysis\n\n"
        f"Dominant failure type: {taxonomy.get('dominant_failure_type', 'unknown')}.\n"
        "This remains a candidate-space diagnosis, not a solved-program-synthesis claim.\n",
        encoding="utf-8",
    )

