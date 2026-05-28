from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.bounded_control_candidate_space_probe import run_candidate_space_probe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--substrate-dataset-dir", default="datasets/v0_9_6_turing_substrate_curriculum")
    parser.add_argument("--frontier-dataset-dir", default="datasets/v0_9_9_turing_frontier_curriculum")
    parser.add_argument("--source-records", default="records/v0_9_8_1")
    parser.add_argument("--output-records", default="records/v0_9_9")
    parser.add_argument("--stages", default="if_else_basic,if_else_nested,bounded_for_loop,bounded_while_with_fuel,nested_bounded_control,bounded_control_hard_supported")
    parser.add_argument("--beam-sizes", default="8,16,32,64,128")
    parser.add_argument("--candidate-budgets", default="32,64,128,256,512")
    parser.add_argument("--template-budgets", default="small,medium,large,xlarge")
    parser.add_argument("--root-expansion-budgets", default="1x,2x,4x,8x")
    parser.add_argument("--memory-budgets", default="baseline,2x,4x,8x")
    parser.add_argument("--samples", type=int, default=5000)
    parser.add_argument("--boundary-samples", type=int, default=5000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--seed", type=int, default=69)
    parser.add_argument("--progress", default="true")
    parser.add_argument("--progress-interval-seconds", type=float, default=2.0)
    args = parser.parse_args()
    result = run_candidate_space_probe(
        args.substrate_dataset_dir,
        args.frontier_dataset_dir,
        args.source_records,
        args.output_records,
        [part.strip() for part in args.stages.split(",") if part.strip()],
        [int(part) for part in args.beam_sizes.split(",") if part.strip()],
        [int(part) for part in args.candidate_budgets.split(",") if part.strip()],
        [part.strip() for part in args.template_budgets.split(",") if part.strip()],
        [part.strip() for part in args.root_expansion_budgets.split(",") if part.strip()],
        [part.strip() for part in args.memory_budgets.split(",") if part.strip()],
        args.samples,
        args.boundary_samples,
        args.compile_worker_count,
        args.run_compiler_validation.lower() == "true",
        args.seed,
    )
    print(json.dumps({
        "candidate_miss_rate": result["coverage"]["candidate_miss_rate"],
        "best_candidate_miss_rate": result["budget"]["candidate_miss_rate_after_best_budget"],
        "compiler_verified_correct_rate": result["compiler"].get("compiler_verified_correct_rate"),
        "recommended_claim_level": result["readiness"]["recommended_claim_level"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

