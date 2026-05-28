from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.clean_msvc_preflight import run_clean_msvc_preflight
from jianmu.self_learning.darwinforge.layerwise_clean_msvc_rerun import run_layerwise_clean_msvc_rerun
from jianmu.self_learning.darwinforge.layerwise_compiler_failure_analysis import write_layerwise_compiler_integrity, write_missing_source_records
from jianmu.self_learning.darwinforge.layerwise_compiler_failure_replay import run_layerwise_failure_replay
from jianmu.self_learning.darwinforge.layerwise_compiler_failure_taxonomy import build_layerwise_compiler_failure_taxonomy
from jianmu.self_learning.darwinforge.layerwise_compiler_readiness import build_layerwise_compiler_readiness, write_layerwise_compiler_mainline


REQUIRED_SOURCE_RECORDS = [
    "compiler_validation_metrics.json",
    "compiler_validation_trace_manifest.json",
    "compiler_validation_trace_layerwise_sparse_1B_freeze_prune.jsonl",
    "adaptive_layerwise_metrics.json",
    "layerwise_access_audit.json",
    "freeze_prune_trace.jsonl",
    "adaptive_layerwise_readiness.json",
    "mainline_conclusion.md",
]


def run_layerwise_compiler_failure_taxonomy_clean_rerun(
    frontier_dataset_dir: str | Path,
    source_records: str | Path,
    output_records: str | Path,
    profile: str = "layerwise_sparse_1B_freeze_prune",
    primary_worker_count: int = 16,
    fallback_worker_counts: tuple[int, ...] = (8, 4),
    supported_samples: int = 3000,
    boundary_samples: int = 3000,
    timeout_seconds: int = 5,
    run_failure_replay: bool = True,
    run_clean_rerun: bool = True,
    progress: bool = True,
    seed: int = 85,
) -> Dict[str, Any]:
    del profile, progress
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    missing = [str(Path(source_records) / name) for name in REQUIRED_SOURCE_RECORDS if not (Path(source_records) / name).exists()]
    if missing:
        return {"readiness": write_missing_source_records(out, missing)}
    preflight = run_clean_msvc_preflight(out, Path.cwd())
    taxonomy = build_layerwise_compiler_failure_taxonomy(source_records, out, preflight.get("antivirus_process_suspected", False) or preflight.get("defender_or_security_lock_suspected", False))
    replay = run_layerwise_failure_replay(frontier_dataset_dir, source_records, out, (primary_worker_count, *fallback_worker_counts[:1]), timeout_seconds) if run_failure_replay else {"failure_replay_completed": False}
    clean = {"clean_rerun_completed": False, "runs": {}, "best_run_label": ""}
    if run_clean_rerun and preflight.get("preflight_passed", False):
        clean = run_layerwise_clean_msvc_rerun(frontier_dataset_dir, out, primary_worker_count, fallback_worker_counts, supported_samples, boundary_samples, timeout_seconds, seed)
    integrity = write_layerwise_compiler_integrity(out)
    readiness = build_layerwise_compiler_readiness(out, taxonomy, replay, clean, integrity)
    conclusion = write_layerwise_compiler_mainline(out, preflight, taxonomy, replay, clean, readiness)
    return {"preflight": preflight, "taxonomy": taxonomy, "replay": replay, "clean": clean, "integrity": integrity, "readiness": readiness, "conclusion": conclusion}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-dataset-dir", required=True)
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--profile", default="layerwise_sparse_1B_freeze_prune")
    parser.add_argument("--primary-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-counts", default="8,4")
    parser.add_argument("--supported-samples", type=int, default=3000)
    parser.add_argument("--boundary-samples", type=int, default=3000)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--run-failure-replay", default="true")
    parser.add_argument("--run-clean-rerun", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--seed", type=int, default=85)
    args = parser.parse_args()
    result = run_layerwise_compiler_failure_taxonomy_clean_rerun(
        args.frontier_dataset_dir,
        args.source_records,
        args.output_records,
        args.profile,
        args.primary_worker_count,
        tuple(int(part) for part in args.fallback_worker_counts.split(",") if part),
        args.supported_samples,
        args.boundary_samples,
        args.timeout_seconds,
        args.run_failure_replay.lower() == "true",
        args.run_clean_rerun.lower() == "true",
        args.progress.lower() == "true",
        args.seed,
    )
    print(json.dumps({
        "recommended_claim_level": result["readiness"]["recommended_claim_level"],
        "dominant_failure_category": result["readiness"].get("dominant_failure_category"),
        "best_clean_run_label": result["readiness"].get("best_clean_run_label"),
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
