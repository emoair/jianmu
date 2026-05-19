import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.datasets.large_architecture_aligned import load_jsonl
from jianmu.self_learning.darwinforge.large_training_probe import (
    LargeDatasetFullTrainingProbeTrainer,
    ProbeConfig,
    write_probe_outputs,
)


def _read_dataset(dataset_dir: Path, eval_sample_limit=None):
    train = load_jsonl(dataset_dir / "jianmu_v0_6_8_train.jsonl")
    eval_by_split = []
    for name in [
        "eval_seen_target_unseen_paraphrase",
        "eval_unseen_target",
        "eval_ood",
    ]:
        eval_by_split.append(load_jsonl(dataset_dir / f"jianmu_v0_6_8_{name}.jsonl"))
    if eval_sample_limit:
        per_split = max(1, eval_sample_limit // len(eval_by_split))
        eval_samples = [sample for rows in eval_by_split for sample in rows[:per_split]]
    else:
        eval_samples = [sample for rows in eval_by_split for sample in rows]
    return train, eval_samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.6.9 Large Dataset Full Training Probe（大数据集全量训练探针）.")
    parser.add_argument("--dataset-dir", type=Path, default=Path("datasets/v0_6_8"))
    parser.add_argument("--mode", choices=["quick", "medium", "full"], default="medium")
    parser.add_argument("--population-per-layer", type=int)
    parser.add_argument("--generations", type=int)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-sample-limit", type=int)
    parser.add_argument("--eval-sample-limit", type=int)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--records-dir", type=Path, default=Path("records/v0_6_9"))
    args = parser.parse_args()

    config = ProbeConfig.for_mode(
        args.mode,
        population_per_layer=args.population_per_layer,
        generations=args.generations,
        top_k=args.top_k,
        seed=args.seed,
        train_sample_limit=args.train_sample_limit,
        eval_sample_limit=args.eval_sample_limit,
        checkpoint_every=args.checkpoint_every,
    )
    train, eval_samples = _read_dataset(args.dataset_dir, config.eval_sample_limit)
    trainer = LargeDatasetFullTrainingProbeTrainer(train, eval_samples, config)
    metrics = trainer.train()
    paths = write_probe_outputs(metrics, args.records_dir)

    before = metrics["before_training_metrics"]["overall"]["target_ir_exact_match"]
    after = metrics["after_combined_metrics"]["overall"]["target_ir_exact_match"]
    eval_by_split = metrics["after_eval_metrics"]["by_split"]
    diag = metrics["after_eval_metrics"]["diagnostics"]
    print(f"mode: {config.mode}")
    print(f"population_per_layer: {config.population_per_layer}")
    print(f"generations: {config.generations}")
    print(f"top_k: {config.top_k}")
    print(f"train sample count: {metrics['train_sample_count']}")
    print(f"eval sample count: {metrics['eval_sample_count']}")
    print(f"before target_ir_exact_match: {before}")
    print(f"after target_ir_exact_match: {after}")
    print(f"train target_ir_exact_match: {metrics['after_train_metrics']['overall']['target_ir_exact_match']}")
    print(f"eval_seen_target_targetir_exact_match: {eval_by_split.get('eval_seen_target_unseen_paraphrase', {}).get('target_ir_exact_match', 0.0)}")
    print(f"eval_unseen_target_targetir_exact_match: {eval_by_split.get('eval_unseen_target', {}).get('target_ir_exact_match', 0.0)}")
    print(f"eval_ood_rejection_rate: {eval_by_split.get('eval_ood', {}).get('unsupported_rejection_rate', 0.0)}")
    print(f"eval_ood_false_accept_rate: {eval_by_split.get('eval_ood', {}).get('false_accept_unsupported_rate', 0.0)}")
    print(f"zh_number_expression_false_reject_rate: {diag['zh_number_expression_false_reject_rate']}")
    print(f"unsupported_arithmetic_false_accept_rate: {diag['unsupported_arithmetic_false_accept_rate']}")
    print(f"candidate_generation_success_rate: {metrics['after_combined_metrics']['overall']['candidate_generation_success_rate']}")
    print(f"runtime seconds: {metrics['runtime_seconds']}")
    print(f"metrics path: {paths['metrics_path']}")
    print(f"report path: {paths['report_path']}")
    print(f"curve path: {paths['curve_path']}")


if __name__ == "__main__":
    main()
