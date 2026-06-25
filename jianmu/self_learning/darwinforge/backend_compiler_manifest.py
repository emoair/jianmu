from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable


REQUIRED_BACKEND_FIELDS = (
    "compile_invocation_id",
    "sample_id",
    "cycle_id",
    "source_sha256",
    "c_source_path",
    "obj_path",
    "exe_path",
    "cl_command",
    "cl_pid",
    "cl_start_monotonic",
    "cl_end_monotonic",
    "cl_returncode",
    "link_command",
    "link_pid",
    "link_start_monotonic",
    "link_end_monotonic",
    "link_returncode",
    "exe_pid",
    "exe_start_monotonic",
    "exe_end_monotonic",
    "exe_returncode",
    "expected_stdout",
    "actual_stdout",
    "stdout_match",
)


def validate_backend_manifest_record(row: Dict[str, object]) -> bool:
    return all(field in row for field in REQUIRED_BACKEND_FIELDS) and not row.get("cached") and not row.get("stubbed")


def write_jsonl(path: str | Path, rows: Iterable[Dict[str, object]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def build_backend_manifest_contract(output_records: str | Path, sample: Dict[str, object]) -> Dict[str, object]:
    result = {
        "backend_manifest_implemented": True,
        "cl_pid_recorded": "cl_pid" in sample,
        "link_pid_recorded": "link_pid" in sample,
        "exe_pid_recorded": "exe_pid" in sample,
        "returncodes_recorded": all(k in sample for k in ("cl_returncode", "link_returncode", "exe_returncode")),
        "artifacts_recorded": all(k in sample for k in ("c_source_path", "obj_path", "exe_path")),
        "stdout_comparison_recorded": "stdout_match" in sample,
        "monotonic_subprocess_timing_recorded": all(k in sample for k in ("cl_start_monotonic", "cl_end_monotonic", "link_start_monotonic", "link_end_monotonic", "exe_start_monotonic", "exe_end_monotonic")),
        "cached_forbidden": sample.get("cached") is False,
        "stubbed_forbidden": sample.get("stubbed") is False,
    }
    result["backend_manifest_contract_passed"] = all(result.values())
    _write_json(Path(output_records) / "backend_compiler_manifest_contract.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

