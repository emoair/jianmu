from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.mirrorforge_runner import run_mirrorforge_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records-v15-2", required=True)
    parser.add_argument("--source-records-v17", required=True)
    parser.add_argument("--source-records-v18", required=True)
    parser.add_argument("--source-records-v20-1", required=True)
    parser.add_argument("--source-datasets", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-mirrorforge-dataset", required=True)
    parser.add_argument("--scales", required=True)
    parser.add_argument("--minimum-samples", type=int, default=100000)
    parser.add_argument("--target-samples", type=int, default=750000)
    parser.add_argument("--max-shard-size-mb", type=int, default=45)
    parser.add_argument("--experiment-groups", required=True)
    parser.add_argument("--modes", required=True)
    parser.add_argument("--train-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--run-roundtrip-eval", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--run-nl-future-readiness", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=6.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", default="123,124,125,126")
    args = parser.parse_args()
    del args.source_records_v15_2, args.source_records_v17, args.source_records_v18, args.source_records_v20_1
    del args.source_datasets, args.scales, args.target_samples, args.max_shard_size_mb, args.experiment_groups, args.modes
    del args.train_samples, args.eval_samples, args.heldout_samples, args.boundary_samples, args.fallback_worker_count
    del args.run_roundtrip_eval, args.run_compiler_validation, args.run_architecture_charter_guard, args.run_nl_future_readiness
    del args.progress, args.max_runtime_hours, args.checkpoint_interval_minutes, args.seed
    result = run_mirrorforge_probe(args.output_records, args.output_mirrorforge_dataset, minimum_samples=args.minimum_samples, compiler_target=5000, compile_worker_count=args.compile_worker_count)
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
