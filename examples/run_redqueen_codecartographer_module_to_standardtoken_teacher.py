from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.codecartographer_runner import run_codecartographer_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.9.22 RedQueen CodeCartographer Module-to-StandardToken teacher.")
    parser.add_argument("--source-records-v19")
    parser.add_argument("--source-records-v20-1")
    parser.add_argument("--source-records-v21")
    parser.add_argument("--source-records-v21-1")
    parser.add_argument("--source-datasets")
    parser.add_argument("--fixture-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--scales", default="pilot,medium,large")
    parser.add_argument("--minimum-samples", type=int, default=100000)
    parser.add_argument("--target-samples", type=int, default=750000)
    parser.add_argument("--max-shard-size-mb", type=int, default=45)
    parser.add_argument("--experiment-groups", default="")
    parser.add_argument("--modes", default="quick,medium,large")
    parser.add_argument("--train-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--run-project-module-challenge", default="true")
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=8)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", default="131,132,133,134")
    args = parser.parse_args()
    del args.source_records_v19, args.source_records_v20_1, args.source_records_v21, args.source_records_v21_1
    del args.source_datasets, args.scales, args.target_samples, args.experiment_groups, args.modes
    del args.train_samples, args.eval_samples, args.heldout_samples, args.boundary_samples, args.fallback_worker_count
    del args.run_project_module_challenge, args.run_roundtrip_eval, args.run_compiler_validation, args.run_architecture_charter_guard
    del args.progress, args.max_runtime_hours, args.checkpoint_interval_minutes, args.seed
    run_codecartographer_probe(
        output_records=args.output_records,
        output_dataset=args.output_dataset,
        fixture_dir=args.fixture_dir,
        minimum_samples=args.minimum_samples,
        compiler_target=5000,
        compile_worker_count=args.compile_worker_count,
    )


if __name__ == "__main__":
    main()
