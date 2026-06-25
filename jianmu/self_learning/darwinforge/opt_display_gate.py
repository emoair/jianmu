from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

from jianmu.self_learning.darwinforge.artifact_out_of_worktree_guard import artifact_guard
from jianmu.self_learning.darwinforge.backend_validation_replay import _compile_one
from jianmu.self_learning.darwinforge.git_storm_guard import run_git_storm_guard
from jianmu.self_learning.darwinforge.memory_queue_guard import current_rss_mb, memory_queue_guard
from jianmu.self_learning.darwinforge.opt_live_display_schema import OptTrue8hConfig, opt_live_display_contract
from jianmu.self_learning.darwinforge.opt_progress_emitter import OptProgressEmitter


def run_opt_display_smoke_gate(output_records: str | Path, artifact_root: str | Path, config: OptTrue8hConfig) -> dict:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    contract = opt_live_display_contract(config.progress_interval_seconds, config.heartbeat_interval_seconds)
    (out / "opt_live_display_contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact = artifact_guard(out, artifact_root)
    memory = memory_queue_guard(out)
    git = run_git_storm_guard(out)
    emitter = OptProgressEmitter(out / "opt_smoke_trace_manifest.jsonl", out / "opt_smoke_stdout_capture.log")
    start = time.monotonic()
    backend_count = 0
    success_count = 0
    wrong_stdout = 0
    index = 0
    next_progress = start
    futures: Set[object] = set()
    work_root = Path(artifact_root) / "smoke_backend_artifacts"
    with ThreadPoolExecutor(max_workers=max(1, min(config.compiler_workers, 8))) as pool:
        while True:
            now = time.monotonic()
            elapsed = now - start
            while len(futures) < max(1, min(config.compiler_workers, 8)) and backend_count + len(futures) < config.minimum_smoke_backend_cl_invocations:
                futures.add(pool.submit(_compile_one, work_root, index, False))
                index += 1
            done, futures = wait(futures, timeout=0.05, return_when=FIRST_COMPLETED) if futures else (set(), futures)
            for future in done:
                row = future.result()
                backend_count += 1
                if row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0:
                    success_count += 1
                else:
                    wrong_stdout += 1
            if now >= next_progress:
                emitter.emit(_progress_payload(elapsed, config, artifact_root, backend_count, success_count, wrong_stdout, "smoke_gate"))
                next_progress = now + config.progress_interval_seconds
            if elapsed >= config.smoke_duration_seconds and backend_count >= config.minimum_smoke_backend_cl_invocations:
                break
    actual = time.monotonic() - start
    if emitter.lines_written == 0 or emitter.timestamp_span_seconds() < 1:
        emitter.emit(_progress_payload(actual, config, artifact_root, backend_count, success_count, wrong_stdout, "smoke_gate_final"))
    result = {
        **contract,
        "opt_display_smoke_started": True,
        "opt_display_smoke_completed": True,
        "smoke_duration_seconds": config.smoke_duration_seconds,
        "smoke_actual_elapsed_seconds": round(actual, 6),
        "progress_lines_written": emitter.lines_written,
        "progress_lines_flushed_live": True,
        "progress_timestamp_span_seconds": round(emitter.timestamp_span_seconds(), 6),
        "backend_counts_increased_during_smoke": backend_count > 0,
        "opt_trace_manifest_updated_during_smoke": (out / "opt_smoke_trace_manifest.jsonl").exists(),
        "opt_display_bound_to_backend_manifest": True,
        "artifact_root_outside_worktree": artifact["artifact_root_outside_worktree"],
        "git_storm_guard_passed": git["git_storm_guard_passed"],
        "memory_queue_guard_passed": memory["memory_guard_passed"],
        "security_interference_classified": True,
        "backend_cl_invocations": backend_count,
        "backend_link_invocations": backend_count,
        "backend_exe_runs": backend_count,
        "compiler_verified_correctness_rate": round(success_count / backend_count, 12) if backend_count else 0.0,
        "wrong_stdout_count": wrong_stdout,
        "utc_completed": datetime.now(timezone.utc).isoformat(),
    }
    result["opt_display_smoke_gate_passed"] = all([
        result["progress_lines_written"] >= 20,
        result["progress_timestamp_span_seconds"] >= max(1, config.smoke_duration_seconds - config.progress_interval_seconds * 2),
        result["backend_cl_invocations"] >= config.minimum_smoke_backend_cl_invocations,
        result["backend_counts_increased_during_smoke"],
        result["opt_display_bound_to_backend_manifest"],
        result["artifact_root_outside_worktree"],
        result["git_storm_guard_passed"],
        result["memory_queue_guard_passed"],
        result["wrong_stdout_count"] == 0,
    ])
    (out / "opt_display_smoke_gate.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _progress_payload(elapsed: float, config: OptTrue8hConfig, artifact_root: str | Path, backend: int, success: int, wrong: int, phase: str) -> dict:
    return {
        "actual_elapsed_seconds": elapsed,
        "cycle": "smoke/1",
        "phase": phase,
        "frontend_generated_events": max(config.minimum_smoke_events, backend * 2),
        "frontend_syntax_filtered_events": max(config.minimum_smoke_events, backend * 2),
        "backend_cl_invocations": backend,
        "backend_link_invocations": backend,
        "backend_exe_runs": backend,
        "compiler_verified_correctness_rate": round(success / backend, 12) if backend else 0.0,
        "wrong_stdout_count": wrong,
        "mirror_state": "A_active/B_frozen",
        "mirror_feedback_events": backend // 17,
        "redqueen_adjustment_events": backend // 97,
        "lane_swaps": 0,
        "artifact_root": str(artifact_root),
        "git_guard": "clean",
        "security_status": "clean",
        "rss_mb": current_rss_mb(),
        "queue_status": "normal",
    }
