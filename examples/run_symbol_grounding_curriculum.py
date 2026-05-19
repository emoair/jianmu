import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.datasets.symbol_grounding import (
    load_symbol_grounding_split,
    write_symbol_grounding_dataset,
)
from jianmu.self_learning.darwinforge.symbol_grounding_trainer import (
    SymbolGroundingConfig,
    SymbolGroundingCurriculumTrainer,
    write_symbol_grounding_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run v0.7.0 Symbol Grounding Curriculum（符号接地课程）.")
    parser.add_argument("--dataset-dir", type=Path, default=Path("datasets/v0_7_0"))
    parser.add_argument("--mode", choices=["quick", "medium", "full"], default="medium")
    parser.add_argument("--population-per-layer", type=int)
    parser.add_argument("--generations", type=int)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--records-dir", type=Path, default=Path("records/v0_7_0"))
    args = parser.parse_args()

    if not (args.dataset_dir / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists():
        write_symbol_grounding_dataset(600 if args.mode == "quick" else 3000, args.seed, args.dataset_dir)
    config = SymbolGroundingConfig.for_mode(
        args.mode,
        population_per_layer=args.population_per_layer,
        generations=args.generations,
        top_k=args.top_k,
        seed=args.seed,
    )
    train = load_symbol_grounding_split(args.dataset_dir, "train")
    eval_samples = load_symbol_grounding_split(args.dataset_dir, "eval")
    ood = load_symbol_grounding_split(args.dataset_dir, "ood")
    trainer = SymbolGroundingCurriculumTrainer(train, eval_samples, ood, config)
    metrics = trainer.train()
    paths = write_symbol_grounding_outputs(metrics, args.records_dir)
    before = metrics["before_metrics"]["symbol_metrics"]
    after = metrics["after_eval_metrics"]["symbol_metrics"]
    print(f"mode: {config.mode}")
    print(f"population_per_layer: {config.population_per_layer}")
    print(f"generations: {config.generations}")
    print(f"top_k: {config.top_k}")
    print(f"train/eval/ood: {metrics['train_sample_count']} / {metrics['eval_sample_count']} / {metrics['ood_sample_count']}")
    print(f"before zh_number_expression_false_reject_rate: {before['zh_number_expression_false_reject_rate']}")
    print(f"after zh_number_expression_false_reject_rate: {after['zh_number_expression_false_reject_rate']}")
    print(f"before zh_number_targetir_exact_match: {before['zh_number_targetir_exact_match']}")
    print(f"after zh_number_targetir_exact_match: {after['zh_number_targetir_exact_match']}")
    print(f"before symbol_slot_accuracy: {before['symbol_slot_accuracy']}")
    print(f"after symbol_slot_accuracy: {after['symbol_slot_accuracy']}")
    print(f"numeral_slot_accuracy: {after['numeral_slot_accuracy']}")
    print(f"operator_slot_accuracy: {after['operator_slot_accuracy']}")
    print(f"paired_arabic_zh_agreement: {after['paired_arabic_zh_agreement']}")
    print(f"paired_group_targetir_consistency: {after['paired_group_targetir_consistency']}")
    print(f"eval target_ir_exact_match: {metrics['after_eval_metrics']['overall']['target_ir_exact_match']}")
    print(f"ood_rejection_rate: {metrics['after_ood_metrics']['overall']['unsupported_rejection_rate']}")
    print(f"ood_false_accept_rate: {metrics['after_ood_metrics']['overall']['false_accept_unsupported_rate']}")
    print(f"report path: {paths['report_path']}")
    print(f"curve path: {paths['curve_path']}")


if __name__ == "__main__":
    main()

