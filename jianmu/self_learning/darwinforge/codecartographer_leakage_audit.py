from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import iter_codecartographer_rows


def run_codecartographer_leakage_audit(dataset_dir: str | Path, output_records: str | Path) -> Dict[str, Any]:
    rows = list(iter_codecartographer_rows(dataset_dir))
    result = {
        "token_contains_expected_output_count": sum(1 for row in rows if row["leakage_guard"]["token_contains_expected_output"]),
        "token_contains_raw_target_ir_json_count": sum(1 for row in rows if row["leakage_guard"]["token_contains_raw_target_ir_json"]),
        "token_contains_c_source_count": sum(1 for row in rows if row["leakage_guard"]["token_contains_c_source"]),
        "target_ir_contains_c_source_count": sum(1 for row in rows if row["leakage_guard"]["target_ir_contains_c_source"]),
        "unsupported_has_targetir_count": sum(1 for row in rows if row["support_status"] == "unsupported" and row["target_ir"] is not None),
        "unsupported_has_expected_output_count": sum(1 for row in rows if row["support_status"] == "unsupported" and row["expected_output"] is not None),
        "leakage_audit_passed": True,
    }
    result["leakage_audit_passed"] = all(value == 0 for key, value in result.items() if key.endswith("_count"))
    _write_json(Path(output_records) / "codecartographer_leakage_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
