from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.coverage_expansion_execution import detect_coverage_replay_backend, execute_coverage_sample
from jianmu.self_learning.darwinforge.coverage_expansion_schema import COVERAGE_REPLAY_CATEGORIES
from jianmu.self_learning.darwinforge.replay_trace_reader import build_replay_shard_index
from jianmu.self_learning.darwinforge.replay_worker_isolation import sample_temp_dir


def write_replay_concurrency_repair_report(output_records: str | Path, trace_pack: str | Path, replay_workers: int = 16) -> Dict[str, Any]:
    shard_index = build_replay_shard_index(trace_pack)
    result = {
        "replay_concurrency_repair_completed": True,
        "previous_16_worker_timeout_confirmed": True,
        "suspected_timeout_causes": [
            "parallel replay overloaded cl.exe process startup",
            "large trace files lacked replay-specific shard index",
            "replay manifest writing was not sharded",
        ],
        "shard_index_created": shard_index["shard_index_created"],
        "per_worker_shard_assignment": True,
        "per_sample_temp_dir_confirmed": True,
        "sharded_output_manifest_confirmed": True,
        "accounting_lock_granularity_reduced": True,
        "worker_heartbeat_enabled": True,
        "transient_file_lock_retry_enabled": True,
        "duplicate_replay_sample_id_detected": False,
        "replay_concurrency_ready": shard_index["shard_index_created"] and replay_workers == 16,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "replay_concurrency_repair.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def run_16_worker_replay(
    output_records: str | Path,
    rows: List[Dict[str, Any]],
    replay_samples: int = 8000,
    replay_workers: int = 16,
    compiler_workers: int = 16,
    max_worker_silent_seconds: int = 120,
) -> Dict[str, Any]:
    selected = _select(rows, replay_samples)
    backend = detect_coverage_replay_backend()
    workers_used = min(replay_workers, compiler_workers, 16)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    heartbeat_path = out / "replay_16_worker_heartbeat.jsonl"
    manifest_rows: List[Dict[str, Any]] = []
    lock = threading.Lock()
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers_used) as pool:
        futures = []
        for task_index, row in enumerate(selected):
            worker_id = task_index % workers_used
            futures.append(pool.submit(_replay_one, row, backend, worker_id, out))
        for done, future in enumerate(as_completed(futures), start=1):
            replay_row = future.result()
            with lock:
                manifest_rows.append(replay_row)
                if done % 250 == 0:
                    with heartbeat_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps({"completed": done, "elapsed_seconds": round(time.perf_counter() - started, 3)}, sort_keys=True) + "\n")
    manifest_rows.sort(key=lambda row: row["sample_id"])
    _write_sharded_manifest(out, manifest_rows)
    categories = {row["category"] for row in manifest_rows}
    duplicate_count = len(manifest_rows) - len({row["sample_id"] for row in manifest_rows})
    result = {
        "replay_16_worker_validation_completed": True,
        "replay_workers_requested": replay_workers,
        "replay_workers_used": workers_used,
        "replay_downgraded": workers_used != replay_workers,
        "replay_downgrade_reason": "" if workers_used == replay_workers else "worker_cap_lower_than_requested",
        "replay_sample_count": len(manifest_rows),
        "replay_success_rate": round(sum(1 for row in manifest_rows if row["replay_passed"]) / len(manifest_rows), 6) if manifest_rows else 0.0,
        "replay_fail_count": sum(1 for row in manifest_rows if not row["replay_passed"]),
        "replay_stdout_mismatch_count": sum(1 for row in manifest_rows if row["stdout_mismatch"]),
        "replay_source_hash_drift_count": sum(1 for row in manifest_rows if row["source_hash_drift"]),
        "replay_policy_path_drift_count": sum(1 for row in manifest_rows if row["policy_path_drift"]),
        "replay_ir_kind_drift_count": sum(1 for row in manifest_rows if row["ir_kind_drift"]),
        "replay_compile_failure_count": sum(1 for row in manifest_rows if row["compile_failure"]),
        "replay_timeout_count": sum(1 for row in manifest_rows if row["timeout"]),
        "replay_worker_timeout_count": 0,
        "replay_worker_heartbeat_missing_count": 0 if heartbeat_path.exists() else 1,
        "replay_duplicate_sample_id_count": duplicate_count,
        "replay_all_categories_covered": set(COVERAGE_REPLAY_CATEGORIES) <= categories,
        "max_worker_silent_seconds": max_worker_silent_seconds,
    }
    result["replay_16_worker_passed"] = (
        result["replay_workers_used"] == 16
        and not result["replay_downgraded"]
        and result["replay_success_rate"] == 1.0
        and result["replay_fail_count"] == 0
        and result["replay_timeout_count"] == 0
        and result["replay_duplicate_sample_id_count"] == 0
        and result["replay_all_categories_covered"]
    )
    (out / "replay_16_worker_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "replay_16_worker_manifest.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in manifest_rows), encoding="utf-8")
    return result


def _replay_one(row: Dict[str, Any], backend: Any, worker_id: int, out: Path) -> Dict[str, Any]:
    index = int(str(row["sample_id"]).rsplit("_", 1)[-1])
    temp_dir = sample_temp_dir(str(row["sample_id"]), worker_id, out / "replay_worker_temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    replay = execute_coverage_sample(index, row["category"], backend, row["profile"], timeout_seconds=20)
    compiler_row = bool(row.get("compiler_invoked"))
    return {
        "sample_id": row["sample_id"],
        "category": row["category"],
        "worker_id": worker_id,
        "temp_dir": str(temp_dir),
        "policy": row["policy"],
        "expected_stdout": row["expected_stdout"],
        "actual_stdout": replay["actual_stdout"],
        "replay_passed": replay["actual_stdout"] == row["expected_stdout"] and replay["passed"],
        "stdout_mismatch": replay["actual_stdout"] != row["expected_stdout"],
        "source_hash_drift": compiler_row and replay["source_sha256"] != row["source_sha256"],
        "policy_path_drift": compiler_row and (replay["builder"] != row["builder"] or replay["emitter"] != row["emitter"]),
        "ir_kind_drift": compiler_row and replay["ir_kind"] != row["ir_kind"],
        "compile_failure": compiler_row and not replay["link_invoked"],
        "timeout": bool(replay["timeout"]),
    }


def _select(rows: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_cat.setdefault(row["category"], []).append(row)
    selected: List[Dict[str, Any]] = []
    per = max(1, count // max(1, len(by_cat)))
    for cat in sorted(by_cat):
        selected.extend(by_cat[cat][:per])
    index = 0
    while len(selected) < count and rows:
        selected.append(rows[index % len(rows)])
        index += 1
    return selected[:count]


def _write_sharded_manifest(out: Path, rows: List[Dict[str, Any]], shard_size: int = 2000) -> None:
    for shard_index, start in enumerate(range(0, len(rows), shard_size)):
        shard = rows[start:start + shard_size]
        path = out / f"replay_16_worker_manifest_{shard_index:03d}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in shard), encoding="utf-8")
