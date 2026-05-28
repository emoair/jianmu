from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_adaptive_layerwise_failure_analysis(output_records: str | Path, layer_audit: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    examples = []
    for row in layer_audit.get("layers", []):
        if row["allocation_status"] == "underpruned":
            examples.append({"failure_type": "underprune_detected", "layer_name": row["layer_name"], "touch_ratio": row["touch_ratio"], "safe_program_preview": "layer diagnostic only"})
    (out / "adaptive_layerwise_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in examples[:50]), encoding="utf-8")
    return {"failure_analysis_completed": True, "example_count": len(examples)}
