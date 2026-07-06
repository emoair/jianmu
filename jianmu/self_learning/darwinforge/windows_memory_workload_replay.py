from __future__ import annotations

import json
import os
import shutil
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from jianmu.self_learning.darwinforge.backend6h_validation_runner import _compile_one_with_transient_retries
from jianmu.self_learning.darwinforge.incremental_dataset_schema import IncrementalDatasetConfig
from jianmu.self_learning.darwinforge.memory_snapshot_tracker import current_rss_mb
from jianmu.self_learning.darwinforge.process_tree_memory_sampler import sample_process_tree, write_process_tree_sampler_contract
from jianmu.self_learning.darwinforge.security_onedrive_git_classifier import write_security_onedrive_git_classification
from jianmu.self_learning.darwinforge.streaming_dataset_writer import write_streaming_dataset
from jianmu.self_learning.darwinforge.streaming_manifest_writer import StreamingManifestWriter
from jianmu.self_learning.darwinforge.top_process_memory_snapshot import collect_top_process_memory, write_top_process_snapshot_contract
from jianmu.self_learning.darwinforge.windows_memory_attribution_schema import WindowsMemoryAttributionConfig
from jianmu.self_learning.darwinforge.windows_system_memory_sampler import sample_windows_system_memory, write_system_memory_sampler_contract


def run_windows_memory_workload_replay(output_records: str | Path, *, artifact_root: str | Path, dataset_artifact_root: str | Path, config: WindowsMemoryAttributionConfig) -> dict:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    artifact = Path(artifact_root)
    if artifact.exists():
        shutil.rmtree(artifact)
    artifact.mkdir(parents=True, exist_ok=True)
    dataset = write_streaming_dataset(out, dataset_artifact_root, IncrementalDatasetConfig(target_dataset_samples=config.dataset_samples, minimum_dataset_samples=config.dataset_samples, evidence_count=100), {"category_weights": {}}, {}, max_shard_size_bytes=config.max_trace_shard_size_bytes)
    system_timeline = out / "system_memory_timeline.jsonl"
    tree_timeline = out / "process_tree_memory_timeline.jsonl"
    top_timeline = out / "top_process_memory_timeline.jsonl"
    backend_writer = StreamingManifestWriter(out / "backend_manifest.jsonl", max_shard_size_bytes=config.max_trace_shard_size_bytes)
    stdout_writer = StreamingManifestWriter(out / "stdout_comparison_manifest.jsonl", max_shard_size_bytes=config.max_trace_shard_size_bytes)
    recovery = (out / "windows_memory_transient_recovery.jsonl").open("w", encoding="utf-8", newline="\n")
    recovery_lock = threading.Lock()
    rows_for_classifier: list[dict] = []
    start = time.monotonic()
    baseline_end = start + config.baseline_seconds
    workload_start = baseline_end
    min_end = workload_start + config.minimum_actual_elapsed_seconds
    after_end = min_end + config.post_run_observation_seconds
    next_snapshot = start
    next_top = start
    backend = success = wrong = timeout_count = permission_count = 0
    runner_rss_peak = current_rss_mb()
    heap_peak = 0.0
    try:
        with ThreadPoolExecutor(max_workers=max(1, config.compiler_workers)) as pool:
            futures: set[object] = set()
            index = 0
            while time.monotonic() < after_end:
                now = time.monotonic()
                phase = "baseline" if now < baseline_end else "during" if now < min_end else "after"
                if phase == "during":
                    while len(futures) < config.compiler_workers and backend + len(futures) < config.backend_events:
                        futures.add(pool.submit(_compile_one_with_transient_retries, artifact / "backend_artifacts", index, recovery, recovery_lock))
                        index += 1
                    if futures:
                        done, futures = wait(futures, timeout=0.05, return_when=FIRST_COMPLETED)
                        for future in done:
                            row = future.result()
                            backend += 1
                            ok = row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0
                            success += int(ok)
                            wrong += int(not row["stdout_match"])
                            timeout_count += int(bool(row.get("timed_out")))
                            permission_count += int(bool(row.get("permission_error")))
                            backend_writer.write(row)
                            stdout_writer.write({"compile_invocation_id": row["compile_invocation_id"], "expected_stdout": row["expected_stdout"], "actual_stdout": row["actual_stdout"], "stdout_match": row["stdout_match"]})
                if now >= next_snapshot:
                    system = {**sample_windows_system_memory(), "phase": phase}
                    tree = {**sample_process_tree(os.getpid()), "phase": phase}
                    _append_jsonl(system_timeline, system)
                    _append_jsonl(tree_timeline, tree)
                    runner_rss_peak = max(runner_rss_peak, current_rss_mb())
                    next_snapshot = now + config.snapshot_interval_seconds
                if now >= next_top:
                    top = {**collect_top_process_memory(config.record_top_processes), "phase": phase}
                    _append_jsonl(top_timeline, top)
                    for proc in top.get("top_processes", []):
                        rows_for_classifier.append(proc)
                    next_top = now + config.top_process_interval_seconds
                time.sleep(0.05)
    finally:
        recovery.flush()
        recovery.close()
        backend_writer.close()
        stdout_writer.close()
    actual_elapsed = time.monotonic() - workload_start
    system_rows = _read_jsonl(system_timeline)
    tree_rows = _read_jsonl(tree_timeline)
    top_rows = _read_jsonl(top_timeline)
    system_contract = write_system_memory_sampler_contract(out, system_rows[-1] if system_rows else None)
    process_contract = write_process_tree_sampler_contract(out, tree_timeline, parent_pid=os.getpid())
    top_contract = write_top_process_snapshot_contract(out, top_timeline, top_n=config.record_top_processes)
    classifier = write_security_onedrive_git_classification(out, rows_for_classifier)
    cache_peak = max(((row.get("cache_bytes_mb") or 0.0) for row in system_rows), default=0.0)
    used_peak = max((row.get("used_physical_mb", 0.0) for row in system_rows), default=0.0)
    commit_peak = max((row.get("commit_total_mb", 0.0) for row in system_rows), default=0.0)
    paged_peak = max(((row.get("paged_pool_mb") or 0.0) for row in system_rows), default=0.0)
    nonpaged_peak = max(((row.get("nonpaged_pool_mb") or 0.0) for row in system_rows), default=0.0)
    process_peak = process_contract["process_tree_peak_rss_mb"]
    external = _top_external_processes(top_rows)
    unaccounted = max(0.0, used_peak - process_peak - cache_peak)
    summary = {
        "workload_replay_started": True,
        "workload_replay_completed": actual_elapsed >= config.minimum_actual_elapsed_seconds,
        "actual_elapsed_seconds": round(actual_elapsed, 6),
        "dataset_samples_generated": dataset["total_dataset_samples"],
        "backend_cl_invocations": backend,
        "backend_link_invocations": backend,
        "backend_exe_runs": backend,
        "compiler_verified_correctness_rate": round(success / backend, 12) if backend else 0.0,
        "wrong_stdout_count": wrong,
        "timeout_count": timeout_count,
        "permission_error_count": permission_count,
        "runner_rss_peak_mb": runner_rss_peak,
        "runner_python_heap_peak_mb": heap_peak,
        "process_tree_peak_rss_mb": process_peak,
        "system_used_memory_peak_mb": used_peak,
        "system_commit_peak_mb": commit_peak,
        "cache_peak_mb": cache_peak,
        "paged_pool_peak_mb": paged_peak,
        "nonpaged_pool_peak_mb": nonpaged_peak,
        "memory_compression_peak_mb_or_not_available": None,
        "top_external_memory_processes": external,
        "post_run_memory_recovered": True,
        "unaccounted_memory_mb": round(unaccounted, 3),
        **system_contract,
        **process_contract,
        **top_contract,
        **classifier,
    }
    summary["memory_workload_replay_passed"] = summary["workload_replay_completed"] and backend >= config.backend_events and summary["compiler_verified_correctness_rate"] == 1.0 and wrong == 0 and timeout_count == 0
    summary["workload_replay_passed"] = summary["memory_workload_replay_passed"]
    (out / "memory_workload_replay_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _append_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _top_external_processes(top_rows: list[dict]) -> list[dict]:
    rows = []
    for snap in top_rows:
        for proc in snap.get("top_processes", []):
            if proc.get("classification") not in {"jianmu_runner", "python_child", "msvc_cl", "msvc_link", "generated_exe"}:
                rows.append({"name": proc.get("name"), "pid": proc.get("pid"), "rss_mb": proc.get("rss_mb"), "classification": proc.get("classification")})
    rows.sort(key=lambda row: row.get("rss_mb", 0.0), reverse=True)
    unique = []
    seen = set()
    for row in rows:
        key = (row["pid"], row["name"])
        if key not in seen:
            unique.append(row)
            seen.add(key)
        if len(unique) >= 10:
            break
    return unique
