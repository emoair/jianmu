from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.arithmetic_training_runner import run_arithmetic_training_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_9_2_arithmetic_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_3")
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--worker-count", type=int, default=4)
    parser.add_argument("--compile-worker-count", type=int, default=2)
    parser.add_argument("--beam-size", type=int, default=8)
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-compiler-spot-audit", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=1.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    args = parser.parse_args()
    result = run_arithmetic_training_probe(args.dataset_dir, args.output_records, [m.strip() for m in args.modes.split(",") if m.strip()], [int(s) for s in args.seeds.split(",") if s.strip()], args.worker_count, args.compile_worker_count, args.beam_size, _flag(args.run_cross_process), _flag(args.run_compiler_spot_audit), args.max_runtime_hours, args.checkpoint_interval_minutes)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
