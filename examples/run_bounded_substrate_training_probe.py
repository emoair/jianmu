from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_substrate_training_runner import child_eval, run_bounded_substrate_training_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--output-records", default="records/v0_9_7")
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--seeds", default="53")
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--beam-size", type=int, default=8)
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=1.0)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=15)
    parser.add_argument("--timeout-seconds", type=int, default=5)
    parser.add_argument("--child-eval", action="store_true")
    parser.add_argument("--state-dir", default="")
    parser.add_argument("--child-output", default="")
    args = parser.parse_args()
    if args.child_eval:
        result = child_eval(args.state_dir, args.child_output)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    result = run_bounded_substrate_training_probe(
        args.dataset_dir,
        args.output_records,
        [part.strip() for part in args.modes.split(",") if part.strip()],
        [int(part) for part in args.seeds.split(",") if part.strip()],
        args.compile_worker_count,
        args.beam_size,
        args.run_cross_process.lower() == "true",
        args.run_compiler_validation.lower() == "true",
        args.timeout_seconds,
    )
    print(json.dumps({
        "modes_completed": result["modes_completed"],
        "supported_candidate_hit_before": result["supported_candidate_hit_before"],
        "supported_candidate_hit_after": result["supported_candidate_hit_after"],
        "top1_supported_correct_before": result["top1_supported_correct_before"],
        "top1_supported_correct_after": result["top1_supported_correct_after"],
        "compiler_verified_correct_rate": result["compiler_verified_correct_rate"],
        "recommended_claim_level": result["recommended_claim_level"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
