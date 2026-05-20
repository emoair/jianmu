import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jianmu.self_learning.darwinforge.canonicalized_training_probe import (
    CanonicalizedTrainingConfig,
    CanonicalizedTrainingProbeTrainer,
    compare_raw_and_canonical,
    write_canonicalized_training_outputs,
)
from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def main():
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    if not (dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        quick_dir = Path("datasets/v0_7_0_quick")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "jianmu.self_learning.datasets.symbol_grounding",
                "--size",
                "600",
                "--seed",
                "42",
                "--out",
                str(quick_dir),
            ],
            check=True,
        )
        dataset_dir = quick_dir
    train = load_symbol_grounding_split(dataset_dir, "train")
    eval_samples = load_symbol_grounding_split(dataset_dir, "eval")
    ood = load_symbol_grounding_split(dataset_dir, "ood")
    overrides = {
        "population_per_layer": args.population_per_layer,
        "generations": args.generations,
        "top_k": args.top_k,
        "seed": args.seed,
        "train_limit": args.train_limit,
        "eval_limit": args.eval_limit,
        "ood_limit": args.ood_limit,
    }
    if args.compare == "both":
        raw_config = CanonicalizedTrainingConfig.for_mode(args.mode, canonicalization_enabled=False, **overrides)
        canonical_config = CanonicalizedTrainingConfig.for_mode(args.mode, canonicalization_enabled=True, **overrides)
        metrics = compare_raw_and_canonical(train, eval_samples, ood, raw_config, canonical_config)
    elif args.compare == "raw":
        raw_config = CanonicalizedTrainingConfig.for_mode(args.mode, canonicalization_enabled=False, **overrides)
        raw = CanonicalizedTrainingProbeTrainer(train, eval_samples, ood, raw_config).train()
        metrics = compare_raw_and_canonical(train, eval_samples, ood, raw_config, raw_config)
        metrics["raw_training"] = {key: value for key, value in raw.items() if key != "candidate_rows"}
    else:
        canonical_config = CanonicalizedTrainingConfig.for_mode(args.mode, canonicalization_enabled=True, **overrides)
        canonical = CanonicalizedTrainingProbeTrainer(train, eval_samples, ood, canonical_config).train()
        metrics = compare_raw_and_canonical(train, eval_samples, ood, canonical_config, canonical_config)
        metrics["canonical_training"] = {key: value for key, value in canonical.items() if key != "candidate_rows"}
    metrics["dataset_dir"] = str(dataset_dir)
    metrics["compare_mode"] = args.compare
    paths = write_canonicalized_training_outputs(metrics, Path(args.records_dir))
    raw_eval = metrics["raw_training"]["after_eval_metrics"]
    can_eval = metrics["canonical_training"]["after_eval_metrics"]
    raw_ood = metrics["raw_training"]["after_ood_metrics"]
    can_ood = metrics["canonical_training"]["after_ood_metrics"]
    print(f"dataset dir: {dataset_dir}")
    print(f"mode: {args.mode}")
    print(f"compare: {args.compare}")
    print(f"population_per_layer: {metrics['canonical_training']['config']['population_per_layer']}")
    print(f"generations: {metrics['canonical_training']['config']['generations']}")
    print(f"top_k: {metrics['canonical_training']['config']['top_k']}")
    print(f"train/eval/ood: {metrics['canonical_training']['train_sample_count']} / {metrics['canonical_training']['eval_sample_count']} / {metrics['canonical_training']['ood_sample_count']}")
    print(f"raw final target_ir_exact_match: {raw_eval['overall']['target_ir_exact_match']}")
    print(f"canonical final target_ir_exact_match: {can_eval['overall']['target_ir_exact_match']}")
    print(f"raw zh_number_expression_false_reject_rate: {raw_eval['zh_number_metrics']['zh_number_expression_false_reject_rate']}")
    print(f"canonical zh_number_expression_false_reject_rate: {can_eval['zh_number_metrics']['zh_number_expression_false_reject_rate']}")
    print(f"raw zh_number_targetir_exact_match: {raw_eval['zh_number_metrics']['zh_number_targetir_exact_match']}")
    print(f"canonical zh_number_targetir_exact_match: {can_eval['zh_number_metrics']['zh_number_targetir_exact_match']}")
    print(f"raw ood_false_accept_rate: {raw_ood['overall']['false_accept_unsupported_rate']}")
    print(f"canonical ood_false_accept_rate: {can_ood['overall']['false_accept_unsupported_rate']}")
    print(f"metrics path: {paths['metrics_path']}")
    print(f"report path: {paths['report_path']}")
    print(f"curve raw path: {paths['curve_raw_path']}")
    print(f"curve canonical path: {paths['curve_canonical_path']}")
    print(f"examples path: {paths['examples_path']}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/v0_7_0")
    parser.add_argument("--mode", choices=["quick", "medium", "full"], default="medium")
    parser.add_argument("--compare", choices=["raw", "canonical", "both"], default="both")
    parser.add_argument("--population-per-layer", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-limit", type=int, default=None)
    parser.add_argument("--eval-limit", type=int, default=None)
    parser.add_argument("--ood-limit", type=int, default=None)
    parser.add_argument("--records-dir", default="records/v0_7_2")
    return parser.parse_args()


if __name__ == "__main__":
    main()
