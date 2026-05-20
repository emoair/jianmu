import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.rootforge_growth_trainer import (
    RootForgeGrowthConfig,
    RootForgeGrowthTrainer,
    write_rootforge_outputs,
)
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    if not (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        quick_dir = Path("datasets/v0_7_0_quick")
        subprocess.run([sys.executable, "-m", "jianmu.self_learning.datasets.symbol_grounding", "--size", "600", "--seed", "42", "--out", str(quick_dir)], check=True)
        dataset_dir = quick_dir
    config = RootForgeGrowthConfig.for_mode(
        args.mode,
        train_limit=args.train_limit,
        eval_limit=args.eval_limit,
        ood_limit=args.ood_limit,
        generations=args.generations,
        beam_size=args.beam_size,
        clone_count_per_layer=args.clone_count_per_layer,
        perturbation_scale=args.perturbation_scale,
        population_per_layer=args.population_per_layer,
        seed=args.seed,
    )
    train = load_symbol_grounding_split(dataset_dir, "train")
    eval_samples = load_symbol_grounding_split(dataset_dir, "eval")
    ood = load_symbol_grounding_split(dataset_dir, "ood")
    metrics = RootForgeGrowthTrainer(train, eval_samples, ood, config).train()
    metrics["dataset_dir"] = str(dataset_dir)
    paths = write_rootforge_outputs(metrics, Path(args.records_dir))
    print(f"dataset dir: {dataset_dir}")
    print(f"mode: {config.mode}")
    print(f"train/eval/ood: {metrics['train_sample_count']} / {metrics['eval_sample_count']} / {metrics['ood_sample_count']}")
    for key in [
        "literal_only_targetir_exact_match",
        "precedence_div_add_success_rate",
        "artifact_suffix_stripped_count",
        "target_ir_exact_match_top1",
        "target_ir_exact_match_beam_oracle",
        "correct_targetir_in_beam_rate",
        "candidate_space_failure_rate",
        "ranking_failure_rate",
        "low_score_correct_count",
        "undervalued_correct_count",
        "lucky_correct_count",
        "regrowth_event_count",
        "regrowth_success_count",
        "necrosis_candidate_count",
        "necrosis_pruned_count",
        "nutrient_contrast_event_count",
        "ood_rejection_rate",
        "ood_false_accept_rate",
    ]:
        print(f"{key}: {metrics.get(key)}")
    print(f"metrics path: {paths['metrics_path']}")
    print(f"report path: {paths['report_path']}")
    print(f"viability path: {paths['viability_path']}")
    print(f"regrowth events path: {paths['regrowth_events_path']}")
    print(f"necrosis events path: {paths['necrosis_events_path']}")
    print(f"annealing path: {paths['annealing_path']}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium"], default="quick")
    parser.add_argument("--train-limit", type=int, default=None)
    parser.add_argument("--eval-limit", type=int, default=None)
    parser.add_argument("--ood-limit", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--beam-size", type=int, default=None)
    parser.add_argument("--clone-count-per-layer", type=int, default=None)
    parser.add_argument("--perturbation-scale", type=float, default=None)
    parser.add_argument("--population-per-layer", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", default="records/v0_7_4")
    return parser.parse_args()


if __name__ == "__main__":
    main()
