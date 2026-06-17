from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


MAX_TRACE_FILE_SIZE_BYTES = 44_000_000
TRACE_WRITE_TARGET_BYTES = 42_000_000


def write_coverage_replay_trace_pack(output_records: str | Path, rows: Iterable[Dict[str, Any]], heartbeats: Iterable[Dict[str, Any]], backend_report: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    pack = out / "coverage_replay_trace_pack"
    pack.mkdir(parents=True, exist_ok=True)
    _clear(pack)
    rows = list(rows)
    heartbeats = list(heartbeats)
    shard_groups = {
        "policy_path_trace": _write_shards(pack, "coverage_replay_policy_path_trace", rows),
        "invocation_manifest": _write_shards(pack, "coverage_replay_invocation_manifest", [_invocation(row) for row in rows]),
        "stdout_comparison_manifest": _write_shards(pack, "coverage_replay_stdout_comparison_manifest", [_stdout(row) for row in rows]),
        "shape_signature_manifest": _write_shards(pack, "coverage_replay_shape_signature_manifest", [_shape(row) for row in rows]),
        "default_blocking_trace": _write_shards(pack, "coverage_replay_default_blocking_trace", [row for row in rows if row.get("category") in {"default_blocking", "malformed_opt_in_blocking", "post_rollback_default_blocking"}]),
        "rollback_trace": _write_shards(pack, "coverage_replay_rollback_trace", [row for row in rows if row.get("category") == "opt_out_rollback"]),
        "sample_id_hashes": _write_shards(pack, "coverage_replay_sample_id_hashes", [{"sample_id": row["sample_id"], "sample_id_hash": _sha256(row["sample_id"])} for row in rows]),
    }
    _write_jsonl(pack / "coverage_replay_guard_heartbeat.jsonl", heartbeats)
    _write_json(pack / "coverage_replay_backend_detection_report.json", backend_report)
    manifest = {
        "coverage_replay_trace_manifest_generated": True,
        "max_trace_file_size_bytes": MAX_TRACE_FILE_SIZE_BYTES,
        "total_rows": len(rows),
        "shard_groups": shard_groups,
    }
    _write_json(pack / "coverage_replay_trace_manifest.json", manifest)
    readiness = {"trace_pack_generated": True, "trace_pack_replayable": bool(rows), "policy_path_trace_generated": bool(rows), "row_count": len(rows)}
    _write_json(pack / "coverage_replay_trace_pack_readiness.json", readiness)
    return readiness


def _clear(pack: Path) -> None:
    for path in pack.glob("coverage_replay_*.jsonl"):
        path.unlink()


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


def _invocation(row: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["sample_id", "category", "profile", "explicit_opt_in", "compile_invocation_id", "cl_invoked", "link_invoked", "exe_run", "cached", "stubbed", "default_profile_modified", "real_promotion_enabled"]
    return {key: row[key] for key in keys}


def _stdout(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: row[key] for key in ["sample_id", "category", "policy", "expected_stdout", "actual_stdout", "passed"]}


def _shape(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: row.get(key) for key in ["sample_id", "category", "shape_signature", "source_sha256", "ir_kind", "builder", "source_shape"]}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
