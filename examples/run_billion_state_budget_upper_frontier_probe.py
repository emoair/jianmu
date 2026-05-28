from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.billion_state_scale_probe import run_billion_state_budget_upper_frontier_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-dataset-dir", default="datasets/v0_9_9_turing_frontier_curriculum")
    parser.add_argument("--source-records", default="records/v0_9_11")
    parser.add_argument("--baseline-records", default="records/v0_9_10")
    parser.add_argument("--output-records", default="records/v0_9_12")
    parser.add_argument("--profiles", default="state_100M_reference,state_300M,state_600M,state_1B")
    parser.add_argument("--samples", type=int, default=15000)
    parser.add_argument("--boundary-samples", type=int, default=15000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--dry-run-first", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=None)
    parser.add_argument("--checkpoint-interval-minutes", type=float, default=None)
    parser.add_argument("--seed", default="77,78,79")
    args = parser.parse_args()
    result = run_billion_state_budget_upper_frontier_probe(
        args.frontier_dataset_dir,
        args.source_records,
        args.baseline_records,
        args.output_records,
        [part.strip() for part in args.profiles.split(",") if part.strip()],
        args.samples,
        args.boundary_samples,
        args.compile_worker_count,
        args.run_compiler_validation.lower() == "true",
        args.run_cross_process.lower() == "true",
        args.progress.lower() == "true",
        args.dry_run_first.lower() == "true",
        args.max_runtime_hours,
        args.checkpoint_interval_minutes,
        [int(part) for part in args.seed.split(",") if part.strip()],
    )
    print(json.dumps({
        "best_profile_name": result["readiness"]["best_profile_name"],
        "state_1B_touch_ratio": result["readiness"]["state_1B_touch_ratio"],
        "top1_1B": result["readiness"]["top1_1B"],
        "recommended_claim_level": result["readiness"]["recommended_claim_level"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

