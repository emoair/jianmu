from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.layerwise_profile_promotion_probe import run_layerwise_profile_promotion_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-dataset-dir", required=True)
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--baseline-records", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--profiles", default="current_1B_reference,combined_hot_rebalanced_balanced_sampling_1B,layerwise_sparse_1B_freeze_prune")
    parser.add_argument("--samples", type=int, default=20000)
    parser.add_argument("--boundary-samples", type=int, default=20000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=None)
    parser.add_argument("--checkpoint-interval-minutes", type=float, default=None)
    parser.add_argument("--seed", default="88,89,90")
    args = parser.parse_args()
    result = run_layerwise_profile_promotion_probe(
        args.frontier_dataset_dir,
        args.source_records,
        args.baseline_records,
        args.output_records,
        [name for name in args.profiles.split(",") if name],
        args.samples,
        args.boundary_samples,
        args.compile_worker_count,
        args.run_compiler_validation.lower() == "true",
        args.run_cross_process.lower() == "true",
        args.progress.lower() == "true",
        args.max_runtime_hours,
        args.checkpoint_interval_minutes,
        [int(seed) for seed in args.seed.split(",") if seed],
    )
    print(json.dumps({
        "recommended_claim_level": result["readiness"].get("recommended_claim_level"),
        "ready_for_default_profile_dry_run": result["readiness"].get("ready_for_default_profile_dry_run"),
        "real_promotion_enabled": result["readiness"].get("real_promotion_enabled"),
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
