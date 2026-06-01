from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.redqueen_v2_large_loop_runner import run_redqueen_v2_large_loop_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records-v20", required=True)
    parser.add_argument("--contrastive-dataset-v20", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-contrastive-full-dataset", required=True)
    parser.add_argument("--experiment-groups", required=True)
    parser.add_argument("--modes", required=True)
    parser.add_argument("--train-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--full-contrastive-materialization-target", type=int, default=750000)
    parser.add_argument("--minimum-materialized-samples", type=int, default=100000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--compiler-validation-target", type=int, default=5000)
    parser.add_argument("--compiler-validation-extended-target", type=int, default=10000)
    parser.add_argument("--run-regression-dashboard", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--run-freeze-readiness", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=6.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", default="119,120,121,122")
    args = parser.parse_args()
    del args.contrastive_dataset_v20, args.experiment_groups, args.modes
    del args.train_samples, args.eval_samples, args.heldout_samples, args.boundary_samples
    del args.full_contrastive_materialization_target, args.minimum_materialized_samples
    del args.fallback_worker_count, args.run_compiler_validation, args.compiler_validation_extended_target
    del args.run_regression_dashboard, args.run_architecture_charter_guard, args.run_freeze_readiness
    del args.progress, args.max_runtime_hours, args.checkpoint_interval_minutes, args.seed
    result = run_redqueen_v2_large_loop_probe(
        args.source_records_v20,
        args.output_records,
        args.output_contrastive_full_dataset,
        compiler_target=args.compiler_validation_target,
        compile_worker_count=args.compile_worker_count,
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
