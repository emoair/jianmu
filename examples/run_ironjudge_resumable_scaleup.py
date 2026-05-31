from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.ironjudge_resumable_runner import run_ironjudge_resumable_scaleup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records", required=True)
    parser.add_argument("--forgefrontier-dataset-dir", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--levels", required=True)
    parser.add_argument("--target-gate", type=int, default=5000)
    parser.add_argument("--target-main", type=int, default=20000)
    parser.add_argument("--target-extended", type=int, default=50000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--resume", default="true")
    parser.add_argument("--run-failure-taxonomy", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=16.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=112)
    args = parser.parse_args()
    del args.fallback_worker_count, args.resume, args.progress, args.checkpoint_interval_minutes
    result = run_ironjudge_resumable_scaleup(
        args.source_records,
        args.forgefrontier_dataset_dir,
        args.output_records,
        [item for item in args.levels.split(",") if item],
        args.target_gate,
        args.target_main,
        args.target_extended,
        args.compile_worker_count,
        args.timeout_seconds,
        args.max_runtime_hours,
        args.seed,
        str(args.run_failure_taxonomy).lower() == "true",
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
