from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.forgefrontier_probe import run_forgefrontier_ironjudge_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-v2-dir")
    parser.add_argument("--chinese-factory-dir")
    parser.add_argument("--redqueen-dataset-dir", required=True)
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-forgefrontier-dataset", required=True)
    parser.add_argument("--experiment-groups", required=True)
    parser.add_argument("--ironjudge-levels", required=True)
    parser.add_argument("--ironjudge-target-invocations", type=int, default=50_000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--train-samples", type=int, default=500_000)
    parser.add_argument("--eval-samples", type=int, default=50_000)
    parser.add_argument("--boundary-samples", type=int, default=50_000)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-ironjudge", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-historical-regression", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=12.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--seed", default="107,108,109,110,111")
    args = parser.parse_args()
    del args.fallback_worker_count, args.train_samples, args.eval_samples, args.boundary_samples, args.run_cross_process, args.run_historical_regression, args.progress, args.checkpoint_interval_minutes, args.seed
    result = run_forgefrontier_ironjudge_probe(
        args.dataset_v2_dir,
        args.chinese_factory_dir,
        args.redqueen_dataset_dir,
        args.source_records,
        args.output_records,
        args.output_forgefrontier_dataset,
        [item for item in args.experiment_groups.split(",") if item],
        [item for item in args.ironjudge_levels.split(",") if item],
        args.ironjudge_target_invocations,
        args.compile_worker_count,
        [item for item in args.modes.split(",") if item],
        str(args.run_compiler_validation).lower() == "true",
        str(args.run_ironjudge).lower() == "true",
        args.max_runtime_hours,
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
