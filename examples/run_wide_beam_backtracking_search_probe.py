import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.wide_beam_backtracking_trainer import (
    WideBeamBacktrackingTrainer,
    WideBeamBacktrackingTrainerConfig,
    write_wide_beam_outputs,
)
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    if not (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        quick_dir = Path("datasets/v0_7_0_quick")
        subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick_dir)], check=True)
        dataset_dir = quick_dir
    overrides = {
        "beam_size": args.beam_size,
        "proposals_per_layer": args.proposals_per_layer,
        "stochastic_samples_per_layer": args.stochastic_samples_per_layer,
        "confidence_noise": args.confidence_noise,
        "clone_count_per_layer": args.clone_count_per_layer,
        "perturbation_scale": args.perturbation_scale,
        "backtracking_window": args.backtracking_window,
        "backtracking_patience": args.backtracking_patience,
        "population_per_layer": args.population_per_layer,
        "generations": args.generations,
        "seed": args.seed,
        "train_limit": args.train_limit,
        "eval_limit": args.eval_limit,
        "ood_limit": args.ood_limit,
    }
    default_config = WideBeamBacktrackingTrainerConfig.for_mode(args.mode)
    config = WideBeamBacktrackingTrainerConfig.for_mode(args.mode, **overrides)
    train = load_symbol_grounding_split(dataset_dir, "train")
    eval_samples = load_symbol_grounding_split(dataset_dir, "eval")
    ood = load_symbol_grounding_split(dataset_dir, "ood")
    metrics = WideBeamBacktrackingTrainer(train, eval_samples, ood, config).train()
    metrics["dataset_dir"] = str(dataset_dir)
    metrics["bounded_runtime_override"] = config.to_dict() != default_config.to_dict()
    paths = write_wide_beam_outputs(metrics, Path(args.records_dir))
    print(f"dataset dir: {dataset_dir}")
    print(f"mode: {config.mode}")
    print(f"beam_size: {config.beam_size}")
    print(f"proposals_per_layer: {config.proposals_per_layer}")
    print(f"stochastic_samples_per_layer: {config.stochastic_samples_per_layer}")
    print(f"confidence_noise: {config.confidence_noise}")
    print(f"clone_count_per_layer: {config.clone_count_per_layer}")
    print(f"perturbation_scale: {config.perturbation_scale}")
    print(f"backtracking_window: {config.backtracking_window}")
    print(f"backtracking_patience: {config.backtracking_patience}")
    print(f"population_per_layer: {config.population_per_layer}")
    print(f"generations: {config.generations}")
    print(f"train/eval/ood: {metrics['train_sample_count']} / {metrics['eval_sample_count']} / {metrics['ood_sample_count']}")
    for key in [
        "target_ir_exact_match_top1",
        "target_ir_exact_match_beam_oracle",
        "beam_oracle_gap",
        "correct_targetir_in_beam_rate",
        "correct_path_in_beam_rate",
        "candidate_space_failure_rate",
        "ranking_failure_rate",
        "upstream_boundary_failure_rate",
        "synthesis_failure_rate",
        "ood_rejection_rate",
        "false_accept_unsupported_rate",
    ]:
        print(f"{key}: {metrics[key]}")
    print(f"metrics path: {paths['metrics_path']}")
    print(f"report path: {paths['report_path']}")
    print(f"diagnostics path: {paths['diagnostics_path']}")
    print(f"candidates path: {paths['candidates_path']}")
    print(f"clone events path: {paths['clone_events_path']}")
    print(f"failure examples path: {paths['failure_examples_path']}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium", "full"], default="medium")
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--proposals-per-layer", type=int, default=None)
    parser.add_argument("--stochastic-samples-per-layer", type=int, default=None)
    parser.add_argument("--confidence-noise", type=float, default=None)
    parser.add_argument("--clone-count-per-layer", type=int, default=None)
    parser.add_argument("--perturbation-scale", type=float, default=None)
    parser.add_argument("--backtracking-window", type=int, default=None)
    parser.add_argument("--backtracking-patience", type=int, default=None)
    parser.add_argument("--population-per-layer", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--train-limit", type=int, default=None)
    parser.add_argument("--eval-limit", type=int, default=None)
    parser.add_argument("--ood-limit", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_3")
    return parser.parse_args()


if __name__ == "__main__":
    main()
