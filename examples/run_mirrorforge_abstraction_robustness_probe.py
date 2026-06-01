from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jianmu.self_learning.darwinforge.mirrorforge_abstraction_runner import run_mirrorforge_abstraction_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.9.21.1 MirrorForge abstraction robustness probe.")
    parser.add_argument("--source-records-v21", default="records/v0_9_21")
    parser.add_argument("--source-mirrorforge-dataset", required=True)
    parser.add_argument("--output-records", required=True)
    parser.add_argument("--output-variant-dataset", required=True)
    parser.add_argument("--variants", default="lossless,semantic,compressed,minimal,noisy")
    parser.add_argument("--ablation-suite", default="full")
    parser.add_argument("--perturbation-suite", default="full")
    parser.add_argument("--experiment-groups", default="")
    parser.add_argument("--modes", default="quick,medium,large")
    parser.add_argument("--train-samples", type=int, default=500000)
    parser.add_argument("--eval-samples", type=int, default=50000)
    parser.add_argument("--heldout-samples", type=int, default=50000)
    parser.add_argument("--boundary-samples", type=int, default=50000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--run-compiler-validation", default="true")
    parser.add_argument("--run-architecture-charter-guard", default="true")
    parser.add_argument("--run-nl-bridge-diagnostic", default="true")
    parser.add_argument("--progress", default="false")
    parser.add_argument("--max-runtime-hours", type=float, default=6)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=10)
    parser.add_argument("--seed", default="127,128,129,130")
    args = parser.parse_args()
    del args.source_records_v21, args.ablation_suite, args.perturbation_suite, args.experiment_groups
    del args.modes, args.train_samples, args.eval_samples, args.heldout_samples, args.boundary_samples
    del args.fallback_worker_count, args.run_compiler_validation, args.run_architecture_charter_guard
    del args.run_nl_bridge_diagnostic, args.progress, args.max_runtime_hours, args.checkpoint_interval_minutes, args.seed
    run_mirrorforge_abstraction_probe(
        source_dataset=args.source_mirrorforge_dataset,
        output_records=args.output_records,
        output_variant_dataset=args.output_variant_dataset,
        variants=[part.strip() for part in args.variants.split(",") if part.strip()],
        compiler_target=5000,
        compile_worker_count=args.compile_worker_count,
    )


if __name__ == "__main__":
    main()
