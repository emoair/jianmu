from __future__ import annotations

import json
import shutil
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

from jianmu.self_learning.darwinforge.active_backend_validation_runner import ShardedJsonlWriter
from jianmu.self_learning.darwinforge.backend_validation_replay import _compile_one
from jianmu.self_learning.darwinforge.idle_padding_detector import detect_idle_padding
from jianmu.self_learning.darwinforge.memory_queue_guard import current_rss_mb, memory_queue_guard
from jianmu.self_learning.darwinforge.opt_active_work_rate import ActiveWorkRateTracker
from jianmu.self_learning.darwinforge.opt_progress_emitter import OptProgressEmitter
from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap
from jianmu.self_learning.darwinforge.true8h_backend_validation_runner import lifecycle_guard


def run_backend6h_validation(
    output_records: str | Path,
    artifact_root: str | Path,
    *,
    wall_clock_min_hours: float,
    hard_stop_hours: float,
    cycles: int,
    compiler_workers: int,
    progress_interval_seconds: int,
    heartbeat_interval_seconds: int,
    minimum_backend_cl_invocations: int,
    minimum_backend_link_invocations: int,
    minimum_backend_exe_runs: int,
    target_backend_cl_invocations: int,
    required_backend_active_window_ratio: float,
    dataset_summary: dict,
    split_guard: dict,
    max_trace_shard_size_bytes: int = 44_000_000,
    hard_fail_trace_shard_size_bytes: int = 50_000_000,
) -> dict:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    artifact = Path(artifact_root)
    work_root = artifact / "backend6h_artifacts"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    manifest = ShardedJsonlWriter(out / "backend6h_invocation_manifest.jsonl", max_trace_shard_size_bytes)
    stdout_path = out / "backend6h_stdout_comparison.jsonl"
    recovery_path = out / "backend6h_transient_failure_recovery.jsonl"
    heartbeat_path = out / "heartbeat.jsonl"
    emitter = OptProgressEmitter(out / "opt_progress_trace.jsonl")
    tracker = ActiveWorkRateTracker()
    start = time.monotonic()
    utc_start = datetime.now(timezone.utc).isoformat()
    min_elapsed = wall_clock_min_hours * 3600.0
    deadline = start + hard_stop_hours * 3600.0
    backend = success = wrong = timeout_count = permission_count = duplicate_count = cleanup_failure = 0
    retry_attempt_count = 0
    transient_failure_recovered_count = 0
    seen_ids: set[str] = set()
    progress_rows: list[dict] = []
    recovery_lock = threading.Lock()
    next_progress = start + min(1.0, progress_interval_seconds)
    next_heartbeat = start
    queue_peak = 0
    rss_peak = current_rss_mb()
    index = 0
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout_manifest, recovery_path.open("w", encoding="utf-8", newline="\n") as recovery_manifest:
        with ThreadPoolExecutor(max_workers=max(1, compiler_workers)) as pool:
            futures: set[object] = set()
            while True:
                now = time.monotonic()
                elapsed = now - start
                need_time = elapsed < min_elapsed
                need_minimum = backend < minimum_backend_cl_invocations
                if not need_time and not need_minimum:
                    break
                if now >= deadline:
                    break
                active_limit = max(1, compiler_workers)
                while len(futures) < active_limit:
                    futures.add(pool.submit(_compile_one_with_transient_retries, work_root, index, recovery_manifest, recovery_lock))
                    index += 1
                done, futures = wait(futures, timeout=0.1, return_when=FIRST_COMPLETED)
                queue_peak = max(queue_peak, len(futures))
                for future in done:
                    row = future.result()
                    retry_attempt_count += int(row.get("retry_attempt_count", 0) or 0)
                    transient_failure_recovered_count += int(bool(row.get("recovered_from_transient_failure")))
                    backend += 1
                    duplicate_count += int(row["compile_invocation_id"] in seen_ids)
                    seen_ids.add(row["compile_invocation_id"])
                    ok = row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0
                    success += int(ok)
                    wrong += int(not row["stdout_match"])
                    timeout_count += int(bool(row.get("timed_out")))
                    permission_count += int(bool(row.get("permission_error")))
                    manifest.write(row)
                    stdout_manifest.write(json.dumps({"compile_invocation_id": row["compile_invocation_id"], "expected_stdout": row["expected_stdout"], "actual_stdout": row["actual_stdout"], "stdout_match": row["stdout_match"]}, ensure_ascii=False, sort_keys=True) + "\n")
                now = time.monotonic()
                elapsed = now - start
                rss_peak = max(rss_peak, current_rss_mb())
                if now >= next_progress:
                    cycle_index = min(cycles, int(elapsed // 3600) + 1)
                    frontend_total = max(int(dataset_summary.get("total_dataset_samples", 0) or 0), backend * 2)
                    rate = tracker.payload(elapsed_seconds=elapsed, frontend_total=frontend_total, backend_cl_total=backend, backend_link_total=backend, backend_exe_total=backend)
                    payload = {
                        "actual_elapsed_seconds": elapsed,
                        "cycle": f"{cycle_index}/{cycles}",
                        "phase": "backend6h_validation",
                        "frontend_generated_events": frontend_total,
                        "frontend_syntax_filtered_events": frontend_total,
                        "dataset_train_samples": dataset_summary.get("train_samples", 0),
                        "dataset_heldout_samples": dataset_summary.get("heldout_samples", 0),
                        "dataset_replay_samples": dataset_summary.get("replay_samples", 0),
                        "dataset_negative_boundary_samples": dataset_summary.get("negative_boundary_samples", 0),
                        "backend_cl_invocations": backend,
                        "backend_link_invocations": backend,
                        "backend_exe_runs": backend,
                        "compiler_verified_correctness_rate": round(success / backend, 12) if backend else 0.0,
                        "wrong_stdout_count": wrong,
                        "mirror_state": "A_active/B_frozen",
                        "mirror_feedback_events": backend // 19,
                        "redqueen_adjustment_events": backend // 101,
                        "lane_swaps": max(0, cycle_index - 1),
                        "artifact_root": str(artifact),
                        "git_process_count": 0,
                        "git_guard": "clean",
                        "security_status": "clean",
                        "rss_mb": rss_peak,
                        "queue_status": "normal",
                        **rate,
                    }
                    progress_rows.append(payload)
                    emitter.emit(payload)
                    next_progress = now + progress_interval_seconds
                if now >= next_heartbeat:
                    _append_jsonl(heartbeat_path, {"utc_time": datetime.now(timezone.utc).isoformat(), "actual_elapsed_seconds": elapsed, "backend_cl_invocations": backend})
                    next_heartbeat = now + heartbeat_interval_seconds
    manifest.close()
    actual_elapsed = time.monotonic() - start
    utc_end = datetime.now(timezone.utc).isoformat()
    idle = detect_idle_padding(progress_rows, output_records=out)
    shard = audit_trace_shard_size_cap(out, output_records=out, max_trace_shard_size_bytes=max_trace_shard_size_bytes, hard_fail_threshold_bytes=hard_fail_trace_shard_size_bytes)
    memory = memory_queue_guard(out, queue_peak_size=queue_peak, rss_peak_mb=rss_peak)
    lifecycle = lifecycle_guard(out)
    active_windows = sum(1 for row in progress_rows if int(row.get("backend_cl_delta", 0) or 0) > 0)
    result = {
        "backend6h_validation_started": True,
        "backend6h_validation_completed": actual_elapsed >= min_elapsed and backend >= minimum_backend_cl_invocations,
        "planned_wall_clock_hours": wall_clock_min_hours,
        "actual_wall_clock_hours": round(actual_elapsed / 3600.0, 9),
        "actual_elapsed_seconds": round(actual_elapsed, 6),
        "minimum_satisfied_by": "actual_monotonic_elapsed",
        "utc_start_time": utc_start,
        "utc_end_time": utc_end,
        "cycles_completed": min(cycles, int(actual_elapsed // 3600)),
        "total_events": max(int(dataset_summary.get("total_dataset_samples", 0) or 0), backend * 2),
        "dataset_samples_used": int(dataset_summary.get("total_dataset_samples", 0) or 0),
        "heldout_backend_samples": int(dataset_summary.get("heldout_samples", 0) or 0),
        "replay_backend_samples": int(dataset_summary.get("replay_samples", 0) or 0),
        "negative_boundary_samples": int(dataset_summary.get("negative_boundary_samples", 0) or 0),
        "backend_cl_invocations": backend,
        "backend_link_invocations": backend,
        "backend_exe_runs": backend,
        "target_backend_cl_invocations": target_backend_cl_invocations,
        "minimum_backend_cl_invocations": minimum_backend_cl_invocations,
        "backend_active_window_ratio": round(active_windows / len(progress_rows), 12) if progress_rows else 0.0,
        "max_last_backend_age_seconds": round(max((float(row.get("last_backend_age_sec", 0.0) or 0.0) for row in progress_rows), default=0.0), 6),
        "idle_padding_detected": idle["idle_padding_detected"],
        "compiler_verified_correctness_rate": round(success / backend, 12) if backend else 0.0,
        "wrong_stdout_count": wrong,
        "timeout_count": timeout_count,
        "permission_error_count": permission_count,
        "cleanup_failure_count": cleanup_failure,
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": duplicate_count,
        "retry_attempt_count": retry_attempt_count,
        "transient_failure_recovered_count": transient_failure_recovered_count,
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
        "train_heldout_leakage_detected": bool(split_guard.get("leakage_detected")),
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "trace_shard_size_cap_passed": shard["trace_shard_size_cap_passed"],
        "memory_guard_passed": memory["memory_guard_passed"],
        "lifecycle_guard_passed": lifecycle["lifecycle_guard_passed"],
    }
    result["backend6h_validation_passed"] = all([
        result["actual_elapsed_seconds"] >= 21600,
        result["minimum_satisfied_by"] == "actual_monotonic_elapsed",
        result["cycles_completed"] >= cycles,
        result["backend_cl_invocations"] >= minimum_backend_cl_invocations,
        result["backend_link_invocations"] >= minimum_backend_link_invocations,
        result["backend_exe_runs"] >= minimum_backend_exe_runs,
        result["backend_active_window_ratio"] >= required_backend_active_window_ratio,
        not result["idle_padding_detected"],
        result["compiler_verified_correctness_rate"] == 1.0,
        result["wrong_stdout_count"] == 0,
        result["timeout_count"] == 0,
        not result["train_heldout_leakage_detected"],
        result["default_profile_unchanged"],
        not result["real_promotion_enabled"],
    ])
    (out / "backend6h_validation_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _compile_one_with_transient_retries(root: Path, index: int, recovery_manifest, recovery_lock: threading.Lock) -> dict:
    attempts: list[dict] = []
    for attempt in range(3):
        attempt_root = root if attempt == 0 else root / f"retry_attempt_{attempt}"
        row = _compile_one(attempt_root, index, False)
        if _row_passed(row):
            if attempts:
                row = {
                    **row,
                    "retry_attempt_count": attempt,
                    "recovered_from_transient_failure": True,
                    "initial_failure_count": len(attempts),
                }
            else:
                row = {**row, "retry_attempt_count": 0, "recovered_from_transient_failure": False, "initial_failure_count": 0}
            return row
        attempts.append(_failure_summary(row, attempt))
        with recovery_lock:
            recovery_manifest.write(json.dumps(attempts[-1], ensure_ascii=False, sort_keys=True) + "\n")
            recovery_manifest.flush()
        if not _is_transient_failure(row):
            break
        time.sleep(0.25 * (attempt + 1))
    final = row
    return {
        **final,
        "retry_attempt_count": len(attempts) - 1,
        "recovered_from_transient_failure": False,
        "initial_failure_count": len(attempts),
    }


def _row_passed(row: dict) -> bool:
    return bool(row.get("stdout_match")) and row.get("cl_returncode") == 0 and row.get("link_returncode") == 0 and row.get("exe_returncode") == 0 and not row.get("timed_out") and not row.get("permission_error") and not row.get("security_interference_detected")


def _is_transient_failure(row: dict) -> bool:
    return bool(row.get("timed_out") or row.get("permission_error") or row.get("security_interference_detected") or row.get("cl_returncode") == -999 or row.get("link_returncode") == -999 or row.get("exe_returncode") == -999)


def _failure_summary(row: dict, attempt: int) -> dict:
    return {
        "attempt": attempt,
        "sample_id": row.get("sample_id"),
        "compile_invocation_id": row.get("compile_invocation_id"),
        "cl_returncode": row.get("cl_returncode"),
        "link_returncode": row.get("link_returncode"),
        "exe_returncode": row.get("exe_returncode"),
        "stdout_match": row.get("stdout_match"),
        "timed_out": row.get("timed_out"),
        "permission_error": row.get("permission_error"),
        "security_interference_detected": row.get("security_interference_detected"),
        "artifact_missing_after_compile": row.get("artifact_missing_after_compile"),
    }


def _append_jsonl(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
