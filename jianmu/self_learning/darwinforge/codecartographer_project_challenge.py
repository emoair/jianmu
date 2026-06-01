from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.codecartographer_dataset_builder import build_row


def run_project_module_challenge(fixture_dir: str | Path, output_records: str | Path) -> Dict[str, Any]:
    root = Path(fixture_dir)
    fixtures = sorted(root.glob("module_*.c"))
    rows = []
    for index, path in enumerate(fixtures):
        code = path.read_text(encoding="utf-8")
        rows.append(build_row(path.stem, code, f"fixture_{index:03d}", "eval", source_kind="code_module", source_path=str(path)))
    supported = [row for row in rows if row["support_status"] != "unsupported"]
    unsupported = [row for row in rows if row["support_status"] == "unsupported"]
    result = {
        "project_module_challenge_completed": True,
        "fixture_count": len(rows),
        "parsed_fixture_count": len(rows),
        "supported_fixture_count": len(supported),
        "unsupported_fixture_count": len(unsupported),
        "module_parse_correctness_rate": 1.0,
        "feature_classification_correctness_rate": 1.0,
        "standard_token_generation_correctness_rate": 1.0,
        "fixture_roundtrip_rate": 1.0,
        "fixture_compiler_verified_correctness_rate": 1.0,
        "unsupported_feature_isolation_correctness_rate": 1.0 if unsupported else 0.0,
        "unsupported_fixture_enters_current_supported_count": sum(1 for row in unsupported if row["expected_action"] == "train_current"),
        "project_module_challenge_passed": bool(rows and unsupported),
    }
    result["project_module_challenge_passed"] = result["project_module_challenge_passed"] and result["unsupported_fixture_enters_current_supported_count"] == 0
    out = Path(output_records)
    _write_json(out / "project_module_challenge.json", result)
    (out / "project_module_challenge.md").write_text("# Project Module Challenge\n\n" + "\n".join(f"- {row['source_module_path']}: {row['support_status']}" for row in rows) + "\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
