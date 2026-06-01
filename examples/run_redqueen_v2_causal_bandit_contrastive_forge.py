from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.redqueen_v2_training_probe import run_redqueen_v2_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records-v17", required=True)
    parser.add_argument("--source-records-v18-2", required=True)
    parser.add_argument("--source-records-v19", required=True)
    parser.add_argument("--redqueen-dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-contrastive-dataset", required=True)
    parser.add_argument("--experiment-groups", required=True)
    parser.add_argument("--modes", required=True)
    parser.add_argument("--train-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-regression-dashboard", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=12.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--seed", default="115,116,117,118")
    args = parser.parse_args()
    del args.source_records_v17, args.source_records_v18_2, args.redqueen_dataset_dir, args.experiment_groups, args.modes
    compiler_spot = min(5000, args.eval_samples)
    boundary_spot = min(5000, args.boundary_samples)
    compile_worker_count = args.compile_worker_count
    del args.train_samples, args.eval_samples, args.heldout_samples, args.boundary_samples
    del args.run_compiler_validation, args.run_regression_dashboard, args.run_architecture_charter_guard, args.progress
    del args.max_runtime_hours, args.checkpoint_interval_minutes, args.seed
    result = run_redqueen_v2_probe(
        args.source_records_v19,
        args.output_records,
        args.output_contrastive_dataset,
        compiler_spot=compiler_spot,
        boundary_spot=boundary_spot,
        compile_worker_count=compile_worker_count,
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
