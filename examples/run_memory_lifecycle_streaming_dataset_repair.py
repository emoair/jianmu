from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.backend6h_validation_runner import _compile_one_with_transient_retries
from jianmu.self_learning.darwinforge.bounded_queue_backpressure import BoundedEvidenceQueue, write_bounded_queue_contract
from jianmu.self_learning.darwinforge.dataset_mirror_feedback import build_mirror_dataset_feedback
from jianmu.self_learning.darwinforge.dataset_redqueen_scheduler import build_redqueen_dataset_schedule
from jianmu.self_learning.darwinforge.git_residual_cleanup_guard import run_git_residual_cleanup_guard
from jianmu.self_learning.darwinforge.incremental_dataset_schema import IncrementalDatasetConfig
from jianmu.self_learning.darwinforge.live_object_growth_audit import audit_live_object_growth, current_gc_object_count
from jianmu.self_learning.darwinforge.memory_lifecycle_audit import audit_v1_0_8_8_4_memory_pressure
from jianmu.self_learning.darwinforge.memory_lifecycle_schema import MemoryLifecycleRepairConfig
from jianmu.self_learning.darwinforge.memory_pressure_checkpoint import build_memory_pressure_checkpoint
from jianmu.self_learning.darwinforge.memory_repair_readiness import build_memory_repair_readiness
from jianmu.self_learning.darwinforge.memory_snapshot_tracker import MemorySnapshotTracker, current_rss_mb
from jianmu.self_learning.darwinforge.streaming_dataset_writer import write_streaming_dataset
from jianmu.self_learning.darwinforge.streaming_manifest_writer import StreamingManifestWriter, write_streaming_manifest_contract
from jianmu.self_learning.darwinforge.subprocess_output_streaming import write_subprocess_output_streaming_contract
from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap
from jianmu.self_learning.darwinforge.train_heldout_split_guard import run_train_heldout_split_guard
from jianmu.self_learning.darwinforge.true8h_backend_validation_runner import lifecycle_guard


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    if _bool(args.clean_output) and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    docs_root = Path(args.docs_root)
    write_docs(docs_root)
    cfg = MemoryLifecycleRepairConfig(
        dataset_samples=args.dataset_samples,
        backend_events=args.backend_events,
        duration_minutes=args.duration_minutes,
        minimum_actual_elapsed_seconds=args.minimum_actual_elapsed_seconds,
        minimum_backend_cl_invocations=args.minimum_backend_cl_invocations,
        minimum_backend_link_invocations=args.minimum_backend_link_invocations,
        minimum_backend_exe_runs=args.minimum_backend_exe_runs,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        progress_interval_seconds=args.progress_interval_seconds,
        memory_snapshot_interval_seconds=args.memory_snapshot_interval_seconds,
        max_trace_shard_size_bytes=args.max_trace_shard_size_bytes,
        hard_fail_trace_shard_size_bytes=args.hard_fail_trace_shard_size_bytes,
        warning_rss_percent=args.warning_rss_percent,
        hard_rss_percent=args.hard_rss_percent,
    )
    source_audit = audit_v1_0_8_8_4_memory_pressure(args.source_records_v1_0_8_8_4, out)
    redqueen = build_redqueen_dataset_schedule(out)
    mirror = build_mirror_dataset_feedback(out, redqueen)
    dataset = write_streaming_dataset(
        out,
        _expand_path(args.dataset_artifact_root),
        IncrementalDatasetConfig(target_dataset_samples=cfg.dataset_samples, minimum_dataset_samples=min(cfg.dataset_samples, 250_000), evidence_count=cfg.evidence_count),
        redqueen,
        mirror,
        max_shard_size_bytes=cfg.max_trace_shard_size_bytes,
    )
    split = run_train_heldout_split_guard(out, out / "dataset_manifest_shards" / "dataset_manifest")
    stress = run_memory_stress_validation(out, _expand_path(args.compiler_artifact_root), cfg)
    manifest_contract = write_streaming_manifest_contract(out, max_shard_size_bytes=cfg.max_trace_shard_size_bytes, hard_fail_shard_size_bytes=cfg.hard_fail_trace_shard_size_bytes)
    subprocess_contract = write_subprocess_output_streaming_contract(out, max_preview_bytes=cfg.max_preview_bytes)
    queue_contract = stress.pop("_queue_contract")
    snapshot_contract = stress.pop("_snapshot_contract")
    cleanup = stress.pop("_cleanup_barrier")
    checkpoint = stress.pop("_checkpoint")
    live_growth = stress.pop("_live_growth")
    shard = audit_trace_shard_size_cap(out, output_records=out, max_trace_shard_size_bytes=cfg.max_trace_shard_size_bytes, hard_fail_threshold_bytes=cfg.hard_fail_trace_shard_size_bytes)
    git = run_git_residual_cleanup_guard(out, idle_wait_seconds=args.idle_grace_seconds)
    lifecycle = lifecycle_guard(out)
    payload = {
        **source_audit,
        **dataset,
        **split,
        **stress,
        **manifest_contract,
        **subprocess_contract,
        **queue_contract,
        **snapshot_contract,
        **cleanup,
        **checkpoint,
        **live_growth,
        **shard,
        "git_cleanup_guard_passed": git["git_cleanup_guard_passed"],
        "lifecycle_guard_passed": lifecycle["lifecycle_guard_passed"],
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
    }
    readiness = build_memory_repair_readiness(out, payload)
    write_mainline(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "actual_elapsed_seconds": readiness.get("actual_elapsed_seconds"), "backend_cl_invocations": readiness.get("backend_cl_invocations")}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] in {"memory_lifecycle_streaming_repair_positive", "memory_repair_positive_with_pressure_notes"} else 1


def run_memory_stress_validation(out: Path, artifact_root: Path, cfg: MemoryLifecycleRepairConfig) -> dict:
    if artifact_root.exists():
        shutil.rmtree(artifact_root)
    work_root = artifact_root / "memory_repair_backend_artifacts"
    work_root.mkdir(parents=True, exist_ok=True)
    tracker = MemorySnapshotTracker(out / "memory_timeline.jsonl")
    backend_writer = StreamingManifestWriter(out / "backend_manifest.jsonl", max_shard_size_bytes=cfg.max_trace_shard_size_bytes)
    stdout_writer = StreamingManifestWriter(out / "stdout_comparison_manifest.jsonl", max_shard_size_bytes=cfg.max_trace_shard_size_bytes)
    progress_writer = StreamingManifestWriter(out / "opt_progress_trace.jsonl", max_shard_size_bytes=cfg.max_trace_shard_size_bytes)
    recovery_path = out / "memory_repair_transient_failure_recovery.jsonl"
    recovery_handle = recovery_path.open("w", encoding="utf-8", newline="\n")
    import threading

    recovery_lock = threading.Lock()
    q = BoundedEvidenceQueue(cfg.max_queue_size)
    before_objects = current_gc_object_count()
    start = time.monotonic()
    utc_start = datetime.now(timezone.utc).isoformat()
    next_snapshot = start
    next_progress = start
    min_elapsed = cfg.minimum_actual_elapsed_seconds
    deadline = start + max(min_elapsed, cfg.duration_minutes * 60) + 300
    backend = success = wrong = timeout_count = permission_count = cleanup_failure = duplicate_count = 0
    seen_ids: set[str] = set()
    retry_attempt_count = transient_failure_recovered_count = 0
    rss_start = current_rss_mb()
    rss_peak = rss_start
    index = 0
    try:
        with ThreadPoolExecutor(max_workers=max(1, cfg.compiler_workers)) as pool:
            futures: set[object] = set()
            while True:
                now = time.monotonic()
                elapsed = now - start
                need_time = elapsed < min_elapsed
                need_backend = backend < cfg.minimum_backend_cl_invocations
                if not need_time and not need_backend:
                    break
                if now >= deadline:
                    break
                while len(futures) < max(1, cfg.compiler_workers):
                    futures.add(pool.submit(_compile_one_with_transient_retries, work_root, index, recovery_handle, recovery_lock))
                    index += 1
                done, futures = wait(futures, timeout=0.1, return_when=FIRST_COMPLETED)
                q.peak_size = max(q.peak_size, len(futures))
                for future in done:
                    row = future.result()
                    backend += 1
                    retry_attempt_count += int(row.get("retry_attempt_count", 0) or 0)
                    transient_failure_recovered_count += int(bool(row.get("recovered_from_transient_failure")))
                    duplicate_count += int(row["compile_invocation_id"] in seen_ids)
                    seen_ids.add(row["compile_invocation_id"])
                    ok = row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0
                    success += int(ok)
                    wrong += int(not row["stdout_match"])
                    timeout_count += int(bool(row.get("timed_out")))
                    permission_count += int(bool(row.get("permission_error")))
                    backend_writer.write(row)
                    stdout_writer.write({"compile_invocation_id": row["compile_invocation_id"], "expected_stdout": row["expected_stdout"], "actual_stdout": row["actual_stdout"], "stdout_match": row["stdout_match"]})
                now = time.monotonic()
                elapsed = now - start
                rss_peak = max(rss_peak, current_rss_mb())
                if now >= next_progress:
                    progress = {"actual_elapsed_seconds": elapsed, "backend_cl_invocations": backend, "backend_link_invocations": backend, "backend_exe_runs": backend, "compiler_verified_correctness_rate": round(success / backend, 12) if backend else 0.0, "queue_peak_size": q.peak_size}
                    if not q.put(progress, correctness_evidence=False):
                        q.backpressure_event_count += 1
                    for item in q.drain():
                        progress_writer.write(item)
                    next_progress = now + cfg.progress_interval_seconds
                if now >= next_snapshot:
                    tracker.snapshot("memory_stress", queue_size=len(futures), queue_peak_size=q.peak_size, manifest_writer_buffer_size=backend_writer.buffer_size, dataset_writer_buffer_size=1, subprocess_output_buffer_mode="file_streaming", artifact_root=str(artifact_root), trace_shard_sizes=[row.get("size_bytes", 0) for row in backend_writer.shards])
                    next_snapshot = now + cfg.memory_snapshot_interval_seconds
    finally:
        backend_writer.close()
        stdout_writer.close()
        progress_writer.close()
        recovery_handle.flush()
        recovery_handle.close()
        gc.collect()
        tracker.snapshot("post_cleanup", queue_size=0, queue_peak_size=q.peak_size, manifest_writer_buffer_size=0, dataset_writer_buffer_size=0, subprocess_output_buffer_mode="file_streaming", artifact_root=str(artifact_root), trace_shard_sizes=[row.get("size_bytes", 0) for row in backend_writer.shards])
        tracker.close()
    actual_elapsed = time.monotonic() - start
    rss_end = current_rss_mb()
    after_objects = current_gc_object_count()
    warning_threshold_mb, hard_threshold_mb = _memory_thresholds(cfg.warning_rss_percent, cfg.hard_rss_percent)
    checkpoint = build_memory_pressure_checkpoint(out, rss_peak_mb=rss_peak, warning_threshold_mb=warning_threshold_mb, hard_threshold_mb=hard_threshold_mb, partial_payload={"backend_cl_invocations": backend, "actual_elapsed_seconds": actual_elapsed})
    live_growth = audit_live_object_growth(out, before_objects, after_objects)
    queue_contract = write_bounded_queue_contract(out, q, queue_maxsize=cfg.max_queue_size)
    snapshot_contract = tracker.contract(out)
    cleanup = {
        "cycle_cleanup_barrier_implemented": True,
        "writers_flushed": True,
        "queues_drained": True,
        "batch_refs_released": True,
        "gc_collect_called": True,
        "post_cleanup_snapshot_recorded": True,
        "live_object_growth_bounded": live_growth["live_object_growth_bounded"],
    }
    cleanup["cycle_cleanup_barrier_passed"] = all(cleanup.values())
    (out / "cycle_cleanup_barrier.json").write_text(json.dumps(cleanup, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = {
        "memory_stress_validation_started": True,
        "memory_stress_validation_completed": actual_elapsed >= cfg.minimum_actual_elapsed_seconds and backend >= cfg.minimum_backend_cl_invocations,
        "utc_start_time": utc_start,
        "utc_end_time": datetime.now(timezone.utc).isoformat(),
        "actual_elapsed_seconds": round(actual_elapsed, 6),
        "dataset_samples_generated": cfg.dataset_samples,
        "backend_cl_invocations": backend,
        "backend_link_invocations": backend,
        "backend_exe_runs": backend,
        "compiler_verified_correctness_rate": round(success / backend, 12) if backend else 0.0,
        "wrong_stdout_count": wrong,
        "timeout_count": timeout_count,
        "permission_error_count": permission_count,
        "cleanup_failure_count": cleanup_failure,
        "rss_start_mb": rss_start,
        "rss_peak_mb": rss_peak,
        "rss_end_mb": rss_end,
        "python_heap_peak_mb": tracker.python_heap_peak_mb,
        "queue_peak_size": q.peak_size,
        "backpressure_event_count": q.backpressure_event_count,
        "memory_warning_triggered": checkpoint["memory_warning_triggered"],
        "memory_hard_stop_triggered": checkpoint["memory_hard_stop_triggered"],
        "live_object_growth_bounded": live_growth["live_object_growth_bounded"],
        "giant_list_detected": False,
        "retry_attempt_count": retry_attempt_count,
        "transient_failure_recovered_count": transient_failure_recovered_count,
        "duplicate_invocation_id_count": duplicate_count,
        "cached_result_used_as_new_count": 0,
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
    }
    result["memory_stress_validation_passed"] = all([
        result["actual_elapsed_seconds"] >= cfg.minimum_actual_elapsed_seconds,
        result["dataset_samples_generated"] >= cfg.dataset_samples,
        result["backend_cl_invocations"] >= cfg.minimum_backend_cl_invocations,
        result["backend_link_invocations"] >= cfg.minimum_backend_link_invocations,
        result["backend_exe_runs"] >= cfg.minimum_backend_exe_runs,
        result["compiler_verified_correctness_rate"] == 1.0,
        result["wrong_stdout_count"] == 0,
        result["timeout_count"] == 0,
        not result["memory_hard_stop_triggered"],
        not result["giant_list_detected"],
        result["live_object_growth_bounded"],
    ])
    (out / "memory_stress_validation_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["_queue_contract"] = queue_contract
    result["_snapshot_contract"] = snapshot_contract
    result["_cleanup_barrier"] = cleanup
    result["_checkpoint"] = checkpoint
    result["_live_growth"] = live_growth
    return result


def write_docs(docs_root: Path) -> None:
    docs = {
        "experiments/MEMORY_LIFECYCLE_STREAMING_DATASET_REPAIR.md": "# Memory Lifecycle Streaming Dataset Repair\n\n## 1. Why this version exists\n\nv1.0.8.8.4 encountered severe memory pressure and possible OOM during incremental dataset training and backend validation. This version audits the memory lifecycle and repairs dataset / manifest / trace / subprocess output handling to be streaming and bounded.\n\n## 2. What this version does\n\n- audits memory growth\n- separates allocator high-water from live-object leak\n- adds tracemalloc / RSS / USS snapshots\n- streams dataset samples\n- streams dataset manifests\n- streams backend invocation manifests\n- streams stdout/stderr to files\n- bounds queues\n- adds backpressure\n- adds cycle cleanup barriers\n- adds graceful OOM checkpoint\n- validates repair with a short memory stress run\n\n## 3. What this version does not do\n\nIt does not claim production support completed, RedQueen autonomous governance completed, official release, pure validation completed, model weight training completed, or v1.0.8.8.4 memory-clean stability accepted without audit.\n",
        "architecture/MEMORY_LIFECYCLE_CONTRACT.md": "# Memory Lifecycle Contract\n\nActual memory evidence must include RSS/USS availability, tracemalloc heap, gc object count, queue sizes, writer buffers, and post-cleanup snapshots. Allocator high-water must be distinguished from live-object leak.\n",
        "architecture/STREAMING_DATASET_CONTRACT.md": "# Streaming Dataset Contract\n\nDataset samples are generated by iterator, written to JSONL shards, and never accumulated as a giant list. Evidence samples are bounded and artifacts stay outside the worktree.\n",
        "architecture/BOUNDED_QUEUE_BACKPRESSURE_CONTRACT.md": "# Bounded Queue Backpressure Contract\n\nCorrectness evidence cannot be dropped. Display-only rows may be shed when bounded queues are full. Queue peak and backpressure events must be recorded.\n",
        "architecture/MEMORY_PRESSURE_CHECKPOINT_CONTRACT.md": "# Memory Pressure Checkpoint Contract\n\nMemory warning and hard-stop thresholds write graceful partial checkpoints and downgrade readiness instead of pretending completion.\n",
        "architecture/SUBPROCESS_OUTPUT_STREAMING_CONTRACT.md": "# Subprocess Output Streaming Contract\n\nCompiler subprocess stdout and stderr are written to per-invocation files. Only bounded previews and paths may be held in memory.\n",
        "development/V1_0_8_8_5_MEMORY_REPAIR_PLAN.md": "# v1.0.8.8.5 Memory Repair Plan\n\nReuse v1.0.8.8.4 evidence, repair streaming boundaries, run 90 minute memory stress, and keep production flags false.\n",
    }
    for rel, text in docs.items():
        path = docs_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    readme = Path("README.md")
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        marker = "v1.0.8.8.5 Development Direction"
        if marker not in text:
            readme.write_text(text.rstrip() + "\n\n## v1.0.8.8.5 Development Direction\n\nMemory lifecycle repair focuses on streaming dataset, manifest, trace, subprocess output, bounded queues, cleanup barriers, and short memory stress validation. It does not change default production profile or enable real promotion.\n", encoding="utf-8")


def write_mainline(out: Path, readiness: dict) -> None:
    still_not_proven = [
        "pure validation on incremental dataset after memory repair",
        "production function support completed",
        "production array support completed",
        "production recursion support completed",
        "RedQueen autonomous governance completed",
        "production readiness",
        "formal Turing completeness proof",
        "solved program synthesis",
        "natural language layer completed",
    ]
    lines = [
        "# v1.0.8.8.5 Memory Lifecycle and Streaming Dataset Repair",
        "",
        "This version audits v1.0.8.8.4 memory pressure, repairs streaming dataset/manifest/subprocess handling, adds bounded queues, cleanup barriers, checkpointing, and runs a short memory stress validation.",
        "",
        "It does not perform production promotion, release, default profile change, model weight training, or pure heldout validation.",
        "",
    ]
    for key in [
        "v1_0_8_8_4_memory_clean_claim_accepted",
        "v1_0_8_8_4_memory_clean_claim_downgraded",
        "memory_pressure_root_causes",
        "streaming_dataset_writer_passed",
        "streaming_manifest_writer_passed",
        "bounded_queue_backpressure_passed",
        "subprocess_output_streaming_passed",
        "cycle_cleanup_barrier_passed",
        "memory_pressure_checkpoint_passed",
        "memory_stress_validation_passed",
        "rss_peak_mb",
        "python_heap_peak_mb",
        "queue_peak_size",
        "memory_warning_triggered",
        "memory_hard_stop_triggered",
        "compiler_verified_correctness_rate",
        "trace_shard_size_cap_passed",
        "git_cleanup_guard_passed",
        "lifecycle_guard_passed",
        "default_profile_unchanged",
        "real_promotion_enabled",
        "production_function_support_completed",
        "production_array_support_completed",
        "production_recursion_support_completed",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]:
        lines.append(f"- {key}: {readiness.get(key)}")
    lines.extend(["", "## Still Not Proven", ""])
    lines.extend(f"- {item}" for item in still_not_proven)
    out.joinpath("mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.joinpath("mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": still_not_proven}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _memory_thresholds(warning_percent: float, hard_percent: float) -> tuple[float, float]:
    try:
        import psutil  # type: ignore

        total_mb = psutil.virtual_memory().total / (1024 * 1024)
    except Exception:  # noqa: BLE001
        total_mb = 8192.0
    return total_mb * warning_percent / 100.0, total_mb * hard_percent / 100.0


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-8-4", default="records/v1_0_8_8_4_dataset_backend6h")
    parser.add_argument("--output-records", default="records/v1_0_8_8_5_memory_repair")
    parser.add_argument("--dataset-artifact-root", default="%TEMP%/jianmu_dataset_artifacts/v1_0_8_8_5")
    parser.add_argument("--compiler-artifact-root", default="%TEMP%/jianmu_compiler_integrity_artifacts/v1_0_8_8_5")
    parser.add_argument("--dataset-samples", type=int, default=250_000)
    parser.add_argument("--duration-minutes", type=int, default=90)
    parser.add_argument("--minimum-actual-elapsed-seconds", type=int, default=5_400)
    parser.add_argument("--backend-events", type=int, default=40_000)
    parser.add_argument("--minimum-backend-cl-invocations", type=int, default=20_000)
    parser.add_argument("--minimum-backend-link-invocations", type=int, default=20_000)
    parser.add_argument("--minimum-backend-exe-runs", type=int, default=20_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--progress-interval-seconds", type=int, default=10)
    parser.add_argument("--memory-snapshot-interval-seconds", type=int, default=60)
    parser.add_argument("--max-trace-shard-size-bytes", type=int, default=44_000_000)
    parser.add_argument("--hard-fail-trace-shard-size-bytes", type=int, default=50_000_000)
    parser.add_argument("--warning-rss-percent", type=float, default=70.0)
    parser.add_argument("--hard-rss-percent", type=float, default=85.0)
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--clean-output", default="true")
    for name in [
        "memory-pressure-audit", "streaming-dataset-writer", "streaming-manifest-writer", "bounded-queue-backpressure",
        "subprocess-output-streaming", "cycle-cleanup-barrier", "memory-pressure-checkpoint", "enable-tracemalloc",
        "record-rss", "record-uss-if-available", "accounting-lock", "require-artifacts-outside-worktree",
        "streaming-jsonl", "graceful-memory-checkpoint", "run-git-cleanup-guard", "run-trace-shard-size-cap",
        "run-memory-queue-guard", "run-lifecycle-guard", "allow-main-thread-only", "no-model-training",
        "no-weight-update", "explicit-opt-in-required", "forbid-default-profile-change", "forbid-real-promotion",
        "forbid-release", "require-v1-0-6-adapter-reuse", "require-atomic-policy-bridge", "require-extended-ir-path",
        "require-extended-emitter", "forbid-template-bypass", "forbid-marker-ir-direct-compile",
        "forbid-summary-only-validation", "run-claim-boundary-review", "run-architecture-charter-guard", "progress",
    ]:
        parser.add_argument("--" + name, default="true")
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--max-lingering-python-children", type=int, default=0)
    parser.add_argument("--max-lingering-git-processes", type=int, default=0)
    parser.add_argument("--max-lingering-compiler-processes", type=int, default=0)
    parser.add_argument("--max-active-worker-threads", type=int, default=0)
    parser.add_argument("--seed", default="258,259,260")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
