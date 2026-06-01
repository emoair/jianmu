from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def run_abstraction_leakage_audit(variant_dataset: str | Path, ir_similarity: Dict[str, Any], output_records: str | Path) -> Dict[str, Any]:
    root = Path(variant_dataset)
    counts = {
        "expected_output_leakage_count": 0,
        "c_source_leakage_count": 0,
        "direct_answer_token_count": 0,
        "mirror_token_contains_raw_target_ir_json_count": 0,
        "mirror_token_contains_expected_output_count": 0,
        "mirror_token_contains_c_source_count": 0,
        "unsupported_future_in_train_current_count": 0,
        "recursion_current_supported_count": 0,
        "pointer_current_supported_count": 0,
        "io_current_supported_count": 0,
    }
    for path in root.glob("*_mirror_token/*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            guard = row.get("leakage_guard", {})
            counts["mirror_token_contains_raw_target_ir_json_count"] += int(guard.get("mirror_token_contains_raw_target_ir_json", False))
            counts["mirror_token_contains_expected_output_count"] += int(guard.get("mirror_token_contains_expected_output", False))
            counts["mirror_token_contains_c_source_count"] += int(guard.get("mirror_token_contains_c_source", False))
            counts["unsupported_future_in_train_current_count"] += int(row.get("support_status") != "current_supported" and row.get("expected_action") == "train_current")
            features = row.get("features", {})
            counts["recursion_current_supported_count"] += int(row.get("support_status") == "current_supported" and features.get("has_recursion", False))
            counts["pointer_current_supported_count"] += int(row.get("support_status") == "current_supported" and features.get("has_pointer", False))
            counts["io_current_supported_count"] += int(row.get("support_status") == "current_supported" and features.get("has_io", False))
    result = {
        **counts,
        "target_ir_structure_similarity_score": ir_similarity["target_ir_structure_similarity_score"],
        "abstraction_risk_score": ir_similarity["abstraction_risk_score"],
        "leakage_audit_passed": all(value == 0 for key, value in counts.items() if key.endswith("_count")),
    }
    out = Path(output_records)
    _write_json(out / "mirrorforge_abstraction_leakage_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
