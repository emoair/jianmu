from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_substrate_larger_training_runner import run_bounded_substrate_larger_training_rerun


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--source-records", default="records/v0_9_7_3")
    parser.add_argument("--output-records", default="records/v0_9_8")
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--seeds", default="63")
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--beam-size", type=int, default=8)
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--progress-interval-seconds", type=float, default=2.0)
    parser.add_argument("--max-runtime-hours", type=float, default=8.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    args = parser.parse_args()
    result = run_bounded_substrate_larger_training_rerun(
        args.dataset_dir,
        args.source_records,
        args.output_records,
        [part.strip() for part in args.modes.split(",") if part.strip()],
        [int(part) for part in args.seeds.split(",") if part.strip()],
        args.compile_worker_count,
        args.beam_size,
        args.run_cross_process.lower() == "true",
        args.run_compiler_validation.lower() == "true",
        args.progress.lower() == "true",
        args.progress_interval_seconds,
        args.max_runtime_hours,
        args.timeout_seconds,
    )
    print(json.dumps({
        "modes_completed": result.get("modes_completed", []),
        "supported_candidate_hit_before": result.get("supported_candidate_hit_before"),
        "supported_candidate_hit_after": result.get("supported_candidate_hit_after"),
        "top1_before": result.get("top1_supported_correct_before"),
        "top1_after": result.get("top1_supported_correct_after"),
        "compiler_verified_correct_rate": result.get("compiler_verified_correct_rate"),
        "progress_events_emitted": result.get("progress_events_emitted"),
        "recommended_claim_level": result.get("recommended_claim_level"),
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

