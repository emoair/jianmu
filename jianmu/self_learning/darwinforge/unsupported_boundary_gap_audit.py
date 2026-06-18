from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_BOUNDARIES = (
    "no explicit opt-in",
    "malformed opt-in flag",
    "disabled opt-in profile",
    "unknown policy",
    "unsupported function shape",
    "unsupported array shape",
    "unsupported recursion shape",
    "pointer-heavy request",
    "malloc/free request",
    "file IO request",
    "multi-file request",
    "arbitrary project parsing request",
    "natural language request",
    "external API request",
    "unbounded recursion",
    "mutual recursion",
    "production promotion request",
    "release request",
)


def audit_unsupported_boundary_gap(source_records: str | Path, output_records: str | Path) -> Dict[str, Any]:
    data = json.loads((Path(source_records) / "unsupported_boundary_matrix.json").read_text(encoding="utf-8"))
    rows = data.get("unsupported_cases", [])
    present = {str(row.get("unsupported_case")) for row in rows}
    missing = [case for case in REQUIRED_BOUNDARIES if case not in present]
    unsafe_compile = sum(1 for row in rows if row.get("compile_invoked") is True)
    result = {
        "unsupported_boundary_audit_completed": True,
        "required_boundary_count": len(REQUIRED_BOUNDARIES),
        "present_boundary_count": len(present & set(REQUIRED_BOUNDARIES)),
        "missing_boundaries": missing,
        "dangerous_boundary_missing": bool(missing),
        "unsafe_compile_allowed_count": unsafe_compile,
        "unsupported_boundary_audit_passed": not missing and unsafe_compile == 0,
    }
    _write_json(Path(output_records) / "unsupported_boundary_gap_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
