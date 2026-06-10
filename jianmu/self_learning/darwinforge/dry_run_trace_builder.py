from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


MAX_TRACE_FILE_SIZE_BYTES = 44_000_000
TRACE_WRITE_TARGET_BYTES = 42_000_000


def write_dry_run_trace_pack(output_records: str | Path, rows: Iterable[Dict[str, Any]], backend_report: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    pack = out / "dry_run_trace_pack"
    pack.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    shards = _write_shards(pack, "dry_run_policy_path_trace", rows)
    _write_jsonl(pack / "dry_run_invocation_manifest.jsonl", (_invocation_row(row) for row in rows))
    _write_jsonl(pack / "dry_run_stdout_comparison_manifest.jsonl", (_stdout_row(row) for row in rows))
    _write_jsonl(pack / "dry_run_sample_id_hashes.jsonl", ({"dry_run_sample_id": row["dry_run_sample_id"], "sample_id_hash": row["sample_id_hash"]} for row in rows))
    _write_json(pack / "dry_run_backend_detection_report.json", backend_report)
    manifest = {
        "dry_run_trace_manifest_generated": True,
        "max_trace_file_size_bytes": MAX_TRACE_FILE_SIZE_BYTES,
        "shards": shards,
        "total_rows": len(rows),
    }
    _write_json(pack / "dry_run_trace_manifest.json", manifest)
    readiness = {
        "trace_pack_generated": True,
        "trace_pack_replayable": bool(rows),
        "policy_path_trace_generated": bool(rows),
        "row_count": len(rows),
    }
    _write_json(pack / "dry_run_trace_pack_readiness.json", readiness)
    return readiness


def _write_shards(pack: Path, prefix: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    shards: List[Dict[str, Any]] = []
    current: List[Dict[str, Any]] = []
    current_size = 0
    index = 0
    for row in rows:
        encoded = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        if current and current_size + len(encoded) > TRACE_WRITE_TARGET_BYTES:
            shards.append(_flush(pack, prefix, index, current))
            index += 1
            current = []
            current_size = 0
        current.append(row)
        current_size += len(encoded)
    if current:
        shards.append(_flush(pack, prefix, index, current))
    return shards


def _flush(pack: Path, prefix: str, index: int, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    path = pack / f"{prefix}_{index:03d}.jsonl"
    _write_jsonl(path, rows)
    return {"path": path.name, "row_count": len(rows), "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _invocation_row(row: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["dry_run_sample_id", "shadow_profile", "policy", "compile_invocation_id", "cl_invoked", "link_invoked", "exe_run", "cached", "stubbed", "production_profile_modified", "real_promotion_enabled"]
    return {key: row[key] for key in keys}


def _stdout_row(row: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["dry_run_sample_id", "policy", "expected_stdout", "actual_stdout", "passed"]
    return {key: row[key] for key in keys}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
