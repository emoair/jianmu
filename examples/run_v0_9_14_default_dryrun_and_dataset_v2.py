from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.darwinforge.layerwise_default_profile_dryrun import run_layerwise_default_profile_dryrun


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-dataset-dir", required=True)
    parser.add_argument("--frontier-v2-dir", required=True)
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--baseline-records", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--profiles", default="actual_current_default_reference,current_1B_reference,combined_hot_rebalanced_balanced_sampling_1B,layerwise_sparse_1B_freeze_prune_dryrun_default")
    parser.add_argument("--samples", type=int, default=20000)
    parser.add_argument("--boundary-samples", type=int, default=20000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-fallback-rollback", default="true")
    parser.add_argument("--run-historical-regression", default="true")
    parser.add_argument("--run-dataset-v2-audit", default="true")
    parser.add_argument("--run-dataset-v2-compiler-spot", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=None)
    parser.add_argument("--checkpoint-interval-minutes", type=float, default=None)
    parser.add_argument("--seed", default="92,93,94")
    args = parser.parse_args()
    del args.progress, args.max_runtime_hours, args.checkpoint_interval_minutes
    result = run_layerwise_default_profile_dryrun(
        args.frontier_dataset_dir,
        args.frontier_v2_dir,
        args.source_records,
        args.baseline_records,
        args.output_records,
        [p for p in args.profiles.split(",") if p],
        args.samples,
        args.boundary_samples,
        args.compile_worker_count,
        args.run_compiler_validation.lower() == "true",
        args.run_cross_process.lower() == "true",
        args.run_fallback_rollback.lower() == "true",
        args.run_historical_regression.lower() == "true",
        args.run_dataset_v2_audit.lower() == "true",
        args.run_dataset_v2_compiler_spot.lower() == "true",
        [int(seed) for seed in args.seed.split(",") if seed],
    )
    print(json.dumps({"recommended_claim_level": result["readiness"]["recommended_claim_level"], "all_v0_9_14_gates_passed": result["readiness"]["all_v0_9_14_gates_passed"], "real_promotion_enabled": result["readiness"]["real_promotion_enabled"]}, indent=2))


if __name__ == "__main__":
    main()
