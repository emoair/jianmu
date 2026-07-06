from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.artifact_cache_pressure_audit import audit_artifact_cache_pressure
from jianmu.self_learning.darwinforge.git_residual_cleanup_guard import run_git_residual_cleanup_guard
from jianmu.self_learning.darwinforge.memory_decay_observer import observe_memory_decay
from jianmu.self_learning.darwinforge.trace_shard_size_cap import audit_trace_shard_size_cap
from jianmu.self_learning.darwinforge.true8h_backend_validation_runner import lifecycle_guard
from jianmu.self_learning.darwinforge.windows_memory_attribution_readiness import build_windows_memory_attribution_readiness
from jianmu.self_learning.darwinforge.windows_memory_attribution_schema import WindowsMemoryAttributionConfig
from jianmu.self_learning.darwinforge.windows_memory_workload_replay import run_windows_memory_workload_replay


def main() -> int:
    args = parse_args()
    out = Path(args.output_records)
    if out.exists() and _bool(args.clean_output):
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    write_docs(Path(args.docs_root))
    cfg = WindowsMemoryAttributionConfig(
        duration_minutes=args.duration_minutes,
        minimum_actual_elapsed_seconds=args.minimum_actual_elapsed_seconds,
        baseline_seconds=args.baseline_seconds,
        post_run_observation_seconds=args.post_run_observation_seconds,
        snapshot_interval_seconds=args.snapshot_interval_seconds,
        top_process_interval_seconds=args.top_process_interval_seconds,
        dataset_samples=args.dataset_samples,
        backend_events=args.backend_events,
        workers=args.workers,
        compiler_workers=args.compiler_workers,
        record_top_processes=args.record_top_processes,
        max_trace_shard_size_bytes=args.max_trace_shard_size_bytes,
        hard_fail_trace_shard_size_bytes=args.hard_fail_trace_shard_size_bytes,
    )
    artifact_root = _expand(args.artifact_root)
    dataset_artifact_root = _expand(args.dataset_artifact_root)
    replay = run_windows_memory_workload_replay(out, artifact_root=artifact_root, dataset_artifact_root=dataset_artifact_root, config=cfg)
    artifact = audit_artifact_cache_pressure(out, compiler_artifact_root=artifact_root, dataset_artifact_root=dataset_artifact_root, records_root=out)
    system_rows = _read_jsonl(out / "system_memory_timeline.jsonl")
    process_rows = _read_jsonl(out / "process_tree_memory_timeline.jsonl")
    decay = observe_memory_decay(out, system_rows, process_rows, observation_seconds=args.post_run_observation_seconds)
    shard = audit_trace_shard_size_cap(out, output_records=out, max_trace_shard_size_bytes=args.max_trace_shard_size_bytes, hard_fail_threshold_bytes=args.hard_fail_trace_shard_size_bytes)
    git = run_git_residual_cleanup_guard(out, idle_wait_seconds=args.idle_grace_seconds)
    lifecycle = lifecycle_guard(out)
    payload = {
        **replay,
        **artifact,
        **decay,
        **shard,
        "git_cleanup_guard_passed": git["git_cleanup_guard_passed"],
        "lifecycle_guard_passed": lifecycle["lifecycle_guard_passed"],
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
    }
    readiness = build_windows_memory_attribution_readiness(out, payload)
    write_mainline(out, readiness)
    print(json.dumps({"recommended_claim_level": readiness["recommended_claim_level"], "primary_attribution": readiness["primary_attribution"], "actual_elapsed_seconds": readiness["actual_elapsed_seconds"]}, ensure_ascii=False, sort_keys=True), flush=True)
    return 0 if readiness["recommended_claim_level"] != "failed" else 1


def write_docs(docs_root: Path) -> None:
    docs = {
        "experiments/WINDOWS_MEMORY_ATTRIBUTION_AUDIT.md": "# Windows Memory Attribution Audit\n\n## 1. Why this version exists\n\nv1.0.8.8.5 repaired Python-level streaming and queue memory issues, but Windows Task Manager still appeared to show high memory usage without an obvious source. This version audits system-level memory attribution.\n\n## 2. What this version does\n\n- distinguishes Python heap from Windows process tree memory\n- captures top process private bytes / working set\n- captures system commit / cache / pool / memory compression\n- classifies Git / IDE / OneDrive / Defender / 360 / MSVC activity\n- tracks artifact file churn and cache pressure\n- records before/during/after memory timelines\n- runs a short workload replay\n- produces an attribution report\n\n## 3. What this version does not do\n\nIt does not claim production support completed, RedQueen autonomous governance completed, official release, memory issue fully solved if attribution remains unknown, or system cache equals Python leak.\n",
        "architecture/WINDOWS_MEMORY_ATTRIBUTION_CONTRACT.md": "# Windows Memory Attribution Contract\n\nSystem memory attribution must distinguish runner memory, child process tree, external scanner/IDE processes, cache/standby, commit, pool, and unaccounted pressure.\n",
        "architecture/PROCESS_TREE_MEMORY_CONTRACT.md": "# Process Tree Memory Contract\n\nRunner PID and child process memory must be sampled separately from global system memory.\n",
        "architecture/SYSTEM_COMMIT_CACHE_POOL_CONTRACT.md": "# System Commit Cache Pool Contract\n\nPhysical memory, commit charge, system cache, paged pool, nonpaged pool, and compression availability must be recorded with fallbacks.\n",
        "architecture/ARTIFACT_CACHE_PRESSURE_CONTRACT.md": "# Artifact Cache Pressure Contract\n\nCompiler artifacts, dataset artifacts, records shards, trace shards, and OneDrive/worktree involvement must be measured for cache pressure.\n",
        "development/V1_0_8_8_6_WINDOWS_MEMORY_PLAN.md": "# v1.0.8.8.6 Windows Memory Plan\n\nReuse v1.0.8.8.5 streaming repair, run a short workload replay, attribute Windows system memory pressure, and keep production flags false.\n",
    }
    for rel, text in docs.items():
        path = docs_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    readme = Path("README.md")
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        marker = "v1.0.8.8.6 Development Direction"
        if marker not in text:
            readme.write_text(text.rstrip() + "\n\n## v1.0.8.8.6 Development Direction\n\nWindows memory attribution distinguishes runner heap/RSS from process tree, system commit/cache/pool, file cache, Git/IDE/OneDrive/security scanner pressure, and unaccounted memory. It does not change default production profile or enable real promotion.\n", encoding="utf-8")


def write_mainline(out: Path, readiness: dict) -> None:
    still_not_proven = [
        "memory issue fully solved if attribution inconclusive",
        "pure validation on incremental dataset after memory repair",
        "production function support completed",
        "production array support completed",
        "production recursion support completed",
        "RedQueen autonomous governance completed",
    ]
    lines = [
        "# v1.0.8.8.6 Windows Memory Attribution Audit",
        "",
        "This version audits Windows system-level memory attribution. v1.0.8.8.5 proved Python-level streaming hygiene, but it did not explain Task Manager-wide memory pressure.",
        "",
    ]
    for key in [
        "runner_rss_peak_mb",
        "runner_python_heap_peak_mb",
        "process_tree_peak_rss_mb",
        "system_used_memory_peak_mb",
        "system_commit_peak_mb",
        "cache_peak_mb",
        "paged_pool_peak_mb",
        "nonpaged_pool_peak_mb",
        "memory_compression_peak_mb_or_not_available",
        "top_external_memory_processes",
        "onedrive_activity_detected",
        "defender_activity_detected",
        "antivirus_360_activity_detected",
        "git_activity_detected",
        "ide_git_activity_detected",
        "file_cache_pressure_suspected",
        "post_run_memory_recovered",
        "unaccounted_memory_mb",
        "primary_attribution",
        "secondary_attributions",
        "attribution_confidence",
        "recommended_fixes",
        "default_profile_unchanged",
        "real_promotion_enabled",
        "production_function_support_completed",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]:
        lines.append(f"- {key}: {readiness.get(key)}")
    lines.extend(["", "## Still Not Proven", ""])
    lines.extend(f"- {item}" for item in still_not_proven)
    out.joinpath("mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.joinpath("mainline_conclusion.json").write_text(json.dumps({"readiness": readiness, "still_not_proven": still_not_proven}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _expand(value: str) -> Path:
    return Path(os.path.expandvars(value))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--source-records-v1-0-8-8-5", default="records/v1_0_8_8_5_memory_repair")
    parser.add_argument("--output-records", default="records/v1_0_8_8_6_windows_memory")
    parser.add_argument("--duration-minutes", type=int, default=30)
    parser.add_argument("--minimum-actual-elapsed-seconds", type=int, default=1800)
    parser.add_argument("--baseline-seconds", type=int, default=60)
    parser.add_argument("--post-run-observation-seconds", type=int, default=180)
    parser.add_argument("--snapshot-interval-seconds", type=int, default=5)
    parser.add_argument("--top-process-interval-seconds", type=int, default=10)
    parser.add_argument("--dataset-samples", type=int, default=100_000)
    parser.add_argument("--backend-events", type=int, default=10_000)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--compiler-workers", type=int, default=16)
    parser.add_argument("--record-top-processes", type=int, default=20)
    parser.add_argument("--artifact-root", default="%TEMP%/jianmu_compiler_integrity_artifacts/v1_0_8_8_6")
    parser.add_argument("--dataset-artifact-root", default="%TEMP%/jianmu_dataset_artifacts/v1_0_8_8_6")
    parser.add_argument("--max-trace-shard-size-bytes", type=int, default=44_000_000)
    parser.add_argument("--hard-fail-trace-shard-size-bytes", type=int, default=50_000_000)
    parser.add_argument("--idle-grace-seconds", type=int, default=30)
    parser.add_argument("--clean-output", default="true")
    for name in [
        "windows-memory-attribution", "system-memory-sampler", "process-tree-memory-sampler",
        "top-process-memory-snapshot", "security-onedrive-git-classifier", "artifact-cache-pressure-audit",
        "memory-decay-observer", "accounting-lock", "record-rss", "record-uss-if-available",
        "record-commit-cache-pool", "record-memory-compression-if-available", "classify-git-ide-onedrive-security",
        "require-artifacts-outside-worktree", "run-git-cleanup-guard", "run-trace-shard-size-cap",
        "run-memory-queue-guard", "run-lifecycle-guard", "allow-main-thread-only", "no-model-training",
        "no-weight-update", "explicit-opt-in-required", "forbid-default-profile-change", "forbid-real-promotion",
        "forbid-release", "run-claim-boundary-review", "run-architecture-charter-guard", "progress",
    ]:
        parser.add_argument("--" + name, default="true")
    parser.add_argument("--trace-writer-mode", default="sharded")
    parser.add_argument("--temp-dir-mode", default="per_sample")
    parser.add_argument("--max-lingering-python-children", type=int, default=0)
    parser.add_argument("--max-lingering-git-processes", type=int, default=0)
    parser.add_argument("--max-lingering-compiler-processes", type=int, default=0)
    parser.add_argument("--max-active-worker-threads", type=int, default=0)
    parser.add_argument("--seed", default="261,262,263")
    return parser.parse_args()


def _bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
