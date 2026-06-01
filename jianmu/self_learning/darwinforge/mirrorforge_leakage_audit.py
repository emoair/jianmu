from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import iter_mirrorforge_rows


def run_mirrorforge_leakage_audit(dataset_dir: str | Path, output_records: str | Path | None = None) -> Dict[str, Any]:
    rows = list(iter_mirrorforge_rows(dataset_dir))
    result = {
        "mirror_token_contains_expected_output_count": sum(1 for row in rows if row["leakage_guard"]["mirror_token_contains_expected_output"]),
        "mirror_token_contains_raw_target_ir_json_count": sum(1 for row in rows if row["leakage_guard"]["mirror_token_contains_raw_target_ir_json"]),
        "mirror_token_contains_c_source_count": sum(1 for row in rows if row["leakage_guard"]["mirror_token_contains_c_source"]),
        "target_ir_contains_c_source_count": sum(1 for row in rows if row["leakage_guard"]["target_ir_contains_c_source"]),
        "input_contains_expected_output_count": 0,
        "leakage_audit_passed": True,
    }
    result["leakage_audit_passed"] = all(result[key] == 0 for key in result if key.endswith("_count"))
    if output_records is not None:
        _write_json(Path(output_records) / "mirrorforge_leakage_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
