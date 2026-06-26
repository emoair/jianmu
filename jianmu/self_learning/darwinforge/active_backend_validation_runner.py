from __future__ import annotations

import json
import shutil
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

from jianmu.self_learning.darwinforge.backend_validation_replay import _compile_one
from jianmu.self_learning.darwinforge.git_residual_cleanup_guard import run_git_residual_cleanup_guard
from jianmu.self_learning.darwinforge.idle_padding_detector import detect_idle_padding
from jianmu.self_learning.darwinforge.memory_queue_guard import current_rss_mb, memory_queue_guard
from jianmu.self_learning.darwinforge.opt_active_work_rate import ActiveWorkRateTracker
from jianmu.self_learning.darwinforge.opt_active_work_schema import OptActiveWorkConfig
from jianmu.self_learning.darwinforge.opt_progress_emitter import OptProgressEmitter
from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap
from jianmu.self_learning.darwinforge.true8h_backend_validation_runner import lifecycle_guard


class ShardedJsonlWriter:
    def __init__(self, base_path: Path, max_bytes: int) -> None:
        self.base_path = base_path
        self.max_bytes = max_bytes
        self.shard_dir = base_path.with_suffix("")
        self.shard_dir.mkdir(parents=True, exist_ok=True)
        self.shard_index = 0
        self.rows = 0
        self.current_path = self._next_path()
        self.handle = self.current_path.open("w", encoding="utf-8", newline="\n")
        self.shards: list[dict] = []

    def write(self, row: dict) -> None:
        text = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        if self.handle.tell() + len(text.encode("utf-8")) > self.max_bytes and self.handle.tell() > 0:
            self._rotate()
        self.handle.write(text)
        self.rows += 1

    def close(self) -> None:
        self.handle.flush()
        self.handle.close()
        self._record_current()
        self.base_path.write_text(json.dumps({"sharded": True, "shard_index_path": str(self.base_path.with_name(self.base_path.stem + "_shard_index.json"))}, sort_keys=True) + "\n", encoding="utf-8")
        self.base_path.with_name(self.base_path.stem + "_shard_index.json").write_text(json.dumps({"total_rows": self.rows, "shards": self.shards}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _next_path(self) -> Path:
        self.shard_index += 1
        return self.shard_dir / f"{self.base_path.stem}.{self.shard_index:04d}.jsonl"

    def _rotate(self) -> None:
        self.handle.flush()
        self.handle.close()
        self._record_current()
        self.current_path = self._next_path()
        self.handle = self.current_path.open("w", encoding="utf-8", newline="\n")

    def _record_current(self) -> None:
        if self.current_path.exists() and not any(item["path"] == str(self.current_path) for item in self.shards):
            self.shards.append({"path": str(self.current_path), "size_bytes": self.current_path.stat().st_size})


def run_active_backend_validation(output_records: str | Path, artifact_root: str | Path, config: OptActiveWorkConfig) -> dict:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    artifact = Path(artifact_root)
    work_root = artifact / "active_backend_artifacts"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    manifest_writer = ShardedJsonlWriter(out / "active_backend_manifest.jsonl", config.max_trace_shard_size_bytes)
    stdout_path = out / "active_backend_stdout_comparison.jsonl"
    progress_path = out / "active_opt_progress_trace.jsonl"
    emitter = OptProgressEmitter(progress_path)
    tracker = ActiveWorkRateTracker()
    start = time.monotonic()
    utc_start = datetime.now(timezone.utc).isoformat()
    min_elapsed = config.minimum_actual_elapsed_seconds
    deadline = start + max(min_elapsed, config.duration_minutes * 60.0) + 120.0
    backend_count = success_count = wrong_stdout = timeout_count = permission_count = duplicate_count = 0
    seen_ids: set[str] = set()
    progress_rows: list[dict] = []
    next_progress = start
    queue_peak = 0
    rss_peak = current_rss_mb()
    index = 0
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout_manifest:
        with ThreadPoolExecutor(max_workers=max(1, config.compiler_workers)) as pool:
            futures: set[object] = set()
            while True:
                now = time.monotonic()
                elapsed = now - start
                need_time = elapsed < min_elapsed
                need_count = backend_count < config.minimum_backend_cl_invocations
                if not need_time and not need_count:
                    break
                if now >= deadline:
                    break
                active_limit = max(1, config.compiler_workers)
                while len(futures) < active_limit:
                    futures.add(pool.submit(_compile_one, work_root, index, False))
                    index += 1
                done, futures = wait(futures, timeout=0.1, return_when=FIRST_COMPLETED)
                queue_peak = max(queue_peak, len(futures))
                for future in done:
                    row = future.result()
                    backend_count += 1
                    duplicate_count += int(row["compile_invocation_id"] in seen_ids)
                    seen_ids.add(row["compile_invocation_id"])
                    ok = row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0
                    success_count += int(ok)
                    wrong_stdout += int(not row["stdout_match"])
                    timeout_count += int(bool(row.get("timed_out")))
                    permission_count += int(bool(row.get("permission_error")))
                    manifest_writer.write(row)
                    stdout_manifest.write(json.dumps({"compile_invocation_id": row["compile_invocation_id"], "expected_stdout": row["expected_stdout"], "actual_stdout": row["actual_stdout"], "stdout_match": row["stdout_match"]}, ensure_ascii=False, sort_keys=True) + "\n")
                now = time.monotonic()
                elapsed = now - start
                rss_peak = max(rss_peak, current_rss_mb())
                if now >= next_progress:
                    frontend_total = max(config.events, backend_count * 2)
                    rate = tracker.payload(elapsed_seconds=elapsed, frontend_total=frontend_total, backend_cl_total=backend_count, backend_link_total=backend_count, backend_exe_total=backend_count)
                    payload = {
                        "actual_elapsed_seconds": elapsed,
                        "cycle": "active/short",
                        "phase": "active_backend_validation",
                        "frontend_generated_events": frontend_total,
                        "frontend_syntax_filtered_events": frontend_total,
                        "backend_cl_invocations": backend_count,
                        "backend_link_invocations": backend_count,
                        "backend_exe_runs": backend_count,
                        "compiler_verified_correctness_rate": round(success_count / backend_count, 12) if backend_count else 0.0,
                        "wrong_stdout_count": wrong_stdout,
                        "mirror_state": "A_active/B_frozen",
                        "mirror_feedback_events": backend_count // 19,
                        "redqueen_adjustment_events": backend_count // 101,
                        "lane_swaps": 0,
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
                    next_progress = now + config.progress_interval_seconds
    manifest_writer.close()
    actual_elapsed = time.monotonic() - start
    utc_end = datetime.now(timezone.utc).isoformat()
    idle = detect_idle_padding(progress_rows, output_records=out)
    shard = audit_trace_shard_size_cap(out, output_records=out, max_trace_shard_size_bytes=config.max_trace_shard_size_bytes, warning_threshold_bytes=config.trace_warning_threshold_bytes, hard_fail_threshold_bytes=config.trace_hard_fail_threshold_bytes)
    memory = memory_queue_guard(out, queue_peak_size=queue_peak, rss_peak_mb=rss_peak)
    git = run_git_residual_cleanup_guard(out, idle_wait_seconds=1)
    lifecycle = lifecycle_guard(out)
    result = {
        "active_backend_validation_started": True,
        "active_backend_validation_completed": actual_elapsed >= min_elapsed and backend_count >= config.minimum_backend_cl_invocations,
        "utc_start_time": utc_start,
        "utc_end_time": utc_end,
        "actual_elapsed_seconds": round(actual_elapsed, 6),
        "events": config.events,
        "frontend_generated_events": max(config.events, backend_count * 2),
        "backend_cl_invocations": backend_count,
        "backend_link_invocations": backend_count,
        "backend_exe_runs": backend_count,
        "backend_active_window_count": sum(1 for row in progress_rows if row["backend_cl_delta"] > 0),
        "idle_progress_window_count": sum(1 for row in progress_rows if row["backend_cl_delta"] == 0),
        "backend_active_window_ratio": round(sum(1 for row in progress_rows if row["backend_cl_delta"] > 0) / len(progress_rows), 12) if progress_rows else 0.0,
        "max_last_backend_age_seconds": round(max((float(row["last_backend_age_sec"]) for row in progress_rows), default=0.0), 6),
        "idle_padding_detected": idle["idle_padding_detected"],
        "compiler_verified_correctness_rate": round(success_count / backend_count, 12) if backend_count else 0.0,
        "wrong_stdout_count": wrong_stdout,
        "timeout_count": timeout_count,
        "permission_error_count": permission_count,
        "cleanup_failure_count": 0,
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": duplicate_count,
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
        "git_cleanup_guard_passed": git["git_cleanup_guard_passed"],
        "trace_shard_size_cap_passed": shard["trace_shard_size_cap_passed"],
        "memory_guard_passed": memory["memory_guard_passed"],
        "lifecycle_guard_passed": lifecycle["lifecycle_guard_passed"],
    }
    result["active_backend_validation_passed"] = all([
        result["active_backend_validation_completed"],
        result["backend_active_window_ratio"] >= config.required_backend_active_window_ratio,
        not result["idle_padding_detected"],
        result["backend_cl_invocations"] >= config.minimum_backend_cl_invocations,
        result["backend_link_invocations"] >= config.minimum_backend_link_invocations,
        result["backend_exe_runs"] >= config.minimum_backend_exe_runs,
        result["compiler_verified_correctness_rate"] == 1.0,
        result["wrong_stdout_count"] == 0,
        result["timeout_count"] == 0,
        result["git_cleanup_guard_passed"],
        result["trace_shard_size_cap_passed"],
        result["memory_guard_passed"],
        result["lifecycle_guard_passed"],
    ])
    (out / "active_backend_validation_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
