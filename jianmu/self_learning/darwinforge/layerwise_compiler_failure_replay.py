from __future__ import annotations

import concurrent.futures
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.bounded_substrate_compiler_temp_manager import validate_sample_with_temp_manager
from jianmu.self_learning.darwinforge.layerwise_compiler_failure_taxonomy import load_layerwise_failures


def run_layerwise_failure_replay(
    frontier_dataset_dir: str | Path,
    source_records: str | Path,
    output_records: str | Path,
    worker_counts: Iterable[int] = (16, 8),
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    failures = load_layerwise_failures(source_records)
    rows_by_hash = _load_rows_by_hash(Path(frontier_dataset_dir) / "large")
    trace: List[Dict[str, Any]] = []
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    remaining = failures
    runs: List[Dict[str, Any]] = []
    for worker_count in worker_counts:
        if not remaining:
            break
        label = f"replay_{worker_count}"
        batch: List[Dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
            slots = itertools.cycle(range(worker_count))
            future_map = {}
            for failure in remaining:
                sample_hash = failure.get("sample_id_hash")
                row = rows_by_hash.get(sample_hash)
                if not row:
                    batch.append(_missing_row_trace(failure, label, worker_count))
                    continue
                future = pool.submit(validate_sample_with_temp_manager, row, out, f"v0_9_12_3_{label}", next(slots), timeout_seconds, backend)
                future_map[future] = failure
            for future in concurrent.futures.as_completed(future_map):
                original = future_map[future]
                item = future.result()
                item.update({
                    "original_failure_type": original.get("failure_category"),
                    "replay_run_label": label,
                    "worker_count": worker_count,
                    "replay_success": bool(item.get("compiler_verified_correct")),
                    "cleanup_failure": bool(item.get("cleanup_failure_count", 0)),
                })
                batch.append(item)
        trace.extend(batch)
        success_hashes = {row.get("sample_id_hash") for row in batch if row.get("replay_success")}
        remaining = [row for row in remaining if row.get("sample_id_hash") not in success_hashes]
        runs.append({
            "replay_run_label": label,
            "worker_count": worker_count,
            "attempted_count": len(batch),
            "success_count": sum(1 for row in batch if row.get("replay_success")),
            "remaining_failure_count": len(remaining),
            "permission_error_count": sum(1 for row in batch if row.get("exception_type") == "PermissionError"),
            "timeout_count": sum(1 for row in batch if row.get("timeout")),
        })
    _write_jsonl(out / "failure_replay_trace.jsonl", trace)
    success_count = len({row.get("sample_id_hash") for row in trace if row.get("replay_success")})
    metrics = {
        "failure_replay_completed": True,
        "original_failure_count": len(failures),
        "replay_success_count": success_count,
        "replay_remaining_failure_count": len(failures) - success_count,
        "runs": runs,
        "real_compiler_invocation_count": sum(1 for row in trace if row.get("compiler_invoked")),
        "permission_error_count": sum(1 for row in trace if row.get("exception_type") == "PermissionError"),
        "cleanup_failure_count": sum(1 for row in trace if row.get("cleanup_failure_count", 0)),
        "timeout_count": sum(1 for row in trace if row.get("timeout")),
    }
    _write_json(out / "failure_replay_metrics.json", metrics)
    return metrics


def _load_rows_by_hash(scale_dir: Path) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    if not scale_dir.exists():
        return rows
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                rows[_hash(row.get("id", ""))] = row
    return rows


def _missing_row_trace(failure: Dict[str, Any], label: str, worker_count: int) -> Dict[str, Any]:
    return {
        "sample_id_hash": failure.get("sample_id_hash"),
        "original_failure_type": failure.get("failure_category"),
        "replay_run_label": label,
        "replay_success": False,
        "worker_count": worker_count,
        "compiler_invoked": False,
        "compile_success": False,
        "runtime_success": False,
        "compiler_verified_correct": False,
        "permission_error_stage": "trace_or_recording_error",
        "exception_type": "MissingSourceSample",
        "exception_message_tail": "sample_id_hash not found in frontier dataset",
        "traceback_tail": "",
        "cleanup_attempted": False,
        "cleanup_success": False,
        "cleanup_retry_count": 0,
        "cleanup_failure": False,
        "notes": "not skipped; source row unavailable",
    }


def _hash(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
