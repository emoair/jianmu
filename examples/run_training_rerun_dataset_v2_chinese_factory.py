from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.training_rerun_dataset_v2_chinese_factory import run_training_rerun_dataset_v2_chinese_factory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-v2-dir", required=True)
    parser.add_argument("--chinese-factory-dir", required=True)
    parser.add_argument("--source-records")
    parser.add_argument("--baseline-records")
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--data-mix-profiles", required=True)
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--train-samples", type=int, default=500_000)
    parser.add_argument("--eval-samples", type=int, default=50_000)
    parser.add_argument("--heldout-samples", type=int, default=50_000)
    parser.add_argument("--boundary-samples", type=int, default=50_000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-historical-regression", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=10.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--seed", default="99,100,101")
    args = parser.parse_args()
    result = run_training_rerun_dataset_v2_chinese_factory(
        args.dataset_v2_dir,
        args.chinese_factory_dir,
        args.output_records,
        [x for x in args.profiles.split(",") if x],
        [x for x in args.data_mix_profiles.split(",") if x],
        [x for x in args.modes.split(",") if x],
        args.train_samples,
        args.eval_samples,
        args.heldout_samples,
        args.boundary_samples,
        args.compile_worker_count,
        str(args.run_compiler_validation).lower() == "true",
    )
    print(json.dumps(result["readiness"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

