from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_tree_allocation_failure_analysis(output_records: str | Path, allocation: Dict[str, Any], dataset: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    examples = []
    for layer in allocation.get("layers", []):
        if layer["allocation_status"] in {"overallocated", "insufficient_data_activation", "intentionally_cold"}:
            examples.append({
                "failure_type": layer["allocation_status"],
                "layer_name": layer["layer_name"],
                "touch_ratio": layer["touch_ratio"],
                "safe_program_preview": "diagnostic layer summary only",
            })
    result = {
        "failure_analysis_completed": True,
        "example_count": len(examples),
        "dataset_underactivation_detected": dataset.get("dataset_underactivation_detected", False),
    }
    (out / "tree_allocation_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples[:50]), encoding="utf-8")
    (out / "tree_allocation_failure_analysis.md").write_text("# Tree Allocation Failure Analysis\n\nExamples are diagnostic layer summaries; no dangerous code is stored.\n", encoding="utf-8")
    return result
