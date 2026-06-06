from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List


TRACE_PATTERNS = ("*trace*.jsonl", "*trace*manifest*.json", "*manifest*.json")


def build_evidence_trace_pack(records_root: str | Path, output_records: str | Path, package_records: str | Path = None, current_trace_records: str | Path = None) -> Dict[str, Any]:
    out = Path(output_records) / "evidence_trace_pack"
    out.mkdir(parents=True, exist_ok=True)
    package_root = Path(package_records) if package_records else Path(records_root) / "audit_v1_0_source_review_suspicion"
    current_root = Path(current_trace_records) if current_trace_records else Path(records_root) / "v0_9_28_1"
    package_traces = _find_traces(package_root)
    current_traces = _find_traces(current_root)
    copied = []
    for path in current_traces:
        copied.append(_copy_or_index(path, out))
    missing = []
    if not package_traces:
        missing.append({"scope": "v1_package", "issue": "raw_trace_missing"})
    _write_jsonl(out / "sample_id_hashes.jsonl", [{"trace_source_path": row["trace_source_path"], "sha256": row["sha256"]} for row in copied])
    _write_jsonl(out / "compile_invocation_manifest.jsonl", [{"trace_source_path": row["trace_source_path"], "artifact_path": row["artifact_path"], "external_artifact_required": row["external_artifact_required"]} for row in copied])
    _write_jsonl(out / "stdout_comparison_manifest.jsonl", [{"trace_source_path": row["trace_source_path"], "stdout_trace_available": "stdout" in row["name"] or "compile" in row["name"]} for row in copied])
    _write_json(out / "backend_detection_report.json", {"source": "existing arithmetic_compiler_backend detection reused", "detected_from_trace_pack_builder": False})
    _write_json(out / "previous_20k_evidence_map.json", {"source": "records/v0_9_27_1 referenced by accounting where present", "package_trace_count": len(package_traces)})
    _write_json(out / "new_30k_or_current_trace_map.json", {"current_workspace_trace_count": len(current_traces), "traces": copied})
    _write_json(out / "missing_trace_files.json", {"missing": missing})
    readiness = {
        "evidence_trace_pack_generated": True,
        "raw_trace_available_in_v1_package": bool(package_traces),
        "raw_trace_available_in_current_workspace": bool(current_traces),
        "package_contains_replayable_full_trace": bool(package_traces),
        "external_artifact_required": any(row["external_artifact_required"] for row in copied),
        "blocking_issues": ["raw_trace_missing"] if not package_traces else [],
    }
    _write_json(out / "trace_pack_readiness.json", readiness)
    _write_json(out.parent / "evidence_trace_pack_readiness.json", readiness)
    _write_json(out / "trace_manifest.json", {"package_traces": [_record(p) for p in package_traces], "current_workspace_traces": copied})
    return readiness


def _find_traces(root: Path) -> List[Path]:
    if not root.exists():
        return []
    found: List[Path] = []
    for pattern in TRACE_PATTERNS:
        found.extend(path for path in root.rglob(pattern) if path.is_file())
    return sorted(set(found))


def _copy_or_index(path: Path, out: Path) -> Dict[str, Any]:
    max_size = 44_000_000
    row = _record(path)
    if path.stat().st_size <= max_size:
        dest = out / path.name
        if dest.resolve() != path.resolve():
            shutil.copy2(str(path), str(dest))
        row.update({"artifact_path": str(dest), "external_artifact_required": False})
    else:
        row.update({"artifact_path": None, "external_artifact_required": True})
    return row


def _record(path: Path) -> Dict[str, Any]:
    return {"name": path.name, "trace_source_path": str(path), "size_bytes": path.stat().st_size, "sha256": _sha256(path)}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

