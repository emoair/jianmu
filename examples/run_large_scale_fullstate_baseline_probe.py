from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.large_scale_fullstate_runner import run_large_scale_fullstate_reproduction


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_8_5_boundary_aware")
    parser.add_argument("--source-records", default="records")
    parser.add_argument("--output-records", default="records/v0_9_1")
    parser.add_argument("--modes", default="quick,medium,large,xlarge,longrun")
    parser.add_argument("--worker-count", type=int, default=8)
    parser.add_argument("--compile-worker-count", type=int, default=4)
    parser.add_argument("--seeds", default="42,43,44,45,46")
    parser.add_argument("--max-runtime-hours", type=float, default=8.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--run-runtime-capture", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-expanded-external-ood", default="true")
    parser.add_argument("--run-multiseed", default="true")
    parser.add_argument("--run-baseline-harness", default="true")
    parser.add_argument("--run-ablation-harness", default="true")
    parser.add_argument("--generate-comparison-pack", default="true")
    args = parser.parse_args()

    result = run_large_scale_fullstate_reproduction(
        dataset_dir=args.dataset_dir,
        source_records=args.source_records,
        output_records=args.output_records,
        modes=[part.strip() for part in args.modes.split(",") if part.strip()],
        worker_count=args.worker_count,
        compile_worker_count=args.compile_worker_count,
        seeds=[int(part.strip()) for part in args.seeds.split(",") if part.strip()],
        max_runtime_hours=args.max_runtime_hours,
        checkpoint_interval_minutes=args.checkpoint_interval_minutes,
        run_runtime_capture=_flag(args.run_runtime_capture),
        run_cross_process=_flag(args.run_cross_process),
        run_expanded_external_ood=_flag(args.run_expanded_external_ood),
        run_multiseed=_flag(args.run_multiseed),
        run_baseline=_flag(args.run_baseline_harness),
        run_ablation=_flag(args.run_ablation_harness),
        generate_comparison_pack=_flag(args.generate_comparison_pack),
    )
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))


def _flag(value: str) -> bool:
    return str(value).lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
