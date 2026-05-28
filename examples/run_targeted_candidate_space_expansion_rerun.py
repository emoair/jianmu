from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.targeted_candidate_space_rerun import run_targeted_candidate_space_rerun


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--substrate-dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--frontier-dataset-dir", default="datasets/v0_9_9_turing_frontier_curriculum")
    parser.add_argument("--source-records", default="records/v0_9_9")
    parser.add_argument("--baseline-records", default="records/v0_9_8_1")
    parser.add_argument("--output-records", default="records/v0_9_10")
    parser.add_argument("--modes", default="quick")
    parser.add_argument("--seeds", default="70")
    parser.add_argument("--beam-size", type=int, default=64)
    parser.add_argument("--candidate-budget", type=int, default=512)
    parser.add_argument("--template-budget", default="xlarge")
    parser.add_argument("--root-expansion-budget", default="8x")
    parser.add_argument("--memory-budget", default="8x")
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--boundary-samples", type=int, default=1000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-cross-process", default="true")
    parser.add_argument("--progress", default="true")
    parser.add_argument("--max-runtime-hours", type=float, default=None)
    parser.add_argument("--checkpoint-interval-minutes", type=float, default=None)
    args = parser.parse_args()
    result = run_targeted_candidate_space_rerun(
        args.substrate_dataset_dir,
        args.frontier_dataset_dir,
        args.source_records,
        args.baseline_records,
        args.output_records,
        [part.strip() for part in args.modes.split(",") if part.strip()],
        [int(part) for part in args.seeds.split(",") if part.strip()],
        args.beam_size,
        args.candidate_budget,
        args.template_budget,
        args.root_expansion_budget,
        args.memory_budget,
        args.samples,
        args.boundary_samples,
        args.compile_worker_count,
        args.run_compiler_validation.lower() == "true",
        args.run_cross_process.lower() == "true",
        args.progress.lower() == "true",
        args.max_runtime_hours,
        args.checkpoint_interval_minutes,
    )
    print(json.dumps({
        "candidate_miss_rate_targeted": result["rerun"]["candidate_miss_rate_targeted"],
        "fresh_ratio": result["rerun"]["fresh_ratio"],
        "compiler_verified_correct_rate": result["compiler"].get("compiler_verified_correct_rate"),
        "recommended_claim_level": result["readiness"]["recommended_claim_level"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

