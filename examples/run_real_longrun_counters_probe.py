from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.real_longrun_runner import run_real_longrun_with_counters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--output-records", default="records/v0_9_1_2")
    parser.add_argument("--modes", default="real-mini")
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--compile-worker-count", type=int, default=2)
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--max-runtime-hours", type=float, default=1.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-real-baseline", default="true")
    parser.add_argument("--run-real-ablation", default="true")
    args = parser.parse_args()
    result = run_real_longrun_with_counters(
        dataset_dir=args.dataset_dir,
        output_records=args.output_records,
        modes=[part.strip() for part in args.modes.split(",") if part.strip()],
        worker_count=args.worker_count,
        compile_worker_count=args.compile_worker_count,
        seeds=[int(part.strip()) for part in args.seeds.split(",") if part.strip()],
        max_runtime_hours=args.max_runtime_hours,
        checkpoint_interval_minutes=args.checkpoint_interval_minutes,
        run_cross_process=_flag(args.run_cross_process),
        run_real_baseline=_flag(args.run_real_baseline),
        run_real_ablation=_flag(args.run_real_ablation),
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
