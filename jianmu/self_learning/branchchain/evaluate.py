import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.branchchain.toy_trainer import BranchChainToyTrainer, evaluate_population


RECORD_DIR = Path("records/v0_5_9")
METRICS_PATH = RECORD_DIR / "branchchain_toy_metrics.json"
REPORT_PATH = RECORD_DIR / "branchchain_toy_report.md"
PREDICTIONS_PATH = RECORD_DIR / "branchchain_toy_predictions.jsonl"


def run_branchchain_toy_experiment(population_size: int = 128, generations: int = 30, seed: int = 42) -> Dict:
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build_branchchain_toy_dataset()
    trainer = BranchChainToyTrainer(population_size=population_size, generations=generations, seed=seed)
    report = trainer.train(dataset)
    metrics = report.to_dict()
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(_report_markdown(metrics), encoding="utf-8")
    _write_predictions(PREDICTIONS_PATH, trainer.population, dataset)
    metrics["report_path"] = str(REPORT_PATH)
    metrics["predictions_path"] = str(PREDICTIONS_PATH)
    return metrics


def _write_predictions(path: Path, population, dataset):
    from jianmu.self_learning.branchchain.branch_chain import BranchChainRouter
    from jianmu.self_learning.branchchain.surface_features import extract_surface_features
    from jianmu.self_learning.branchchain.toy_trainer import build_target_from_branch_path

    router = BranchChainRouter(population)
    rows = []
    for sample in dataset:
        features = extract_surface_features(sample["input_text"])
        branch_path = router.route(features)
        target_ir, output = build_target_from_branch_path(branch_path, features)
        rows.append(
            {
                "sample_id": sample["sample_id"],
                "input_text": sample["input_text"],
                "branch_path": branch_path.to_dict(),
                "target_branch_path": sample["target_branch_path"],
                "target_ir_pred": target_ir,
                "target_ir_true": sample["target_ir_canonical"],
                "expected_output_pred": output,
                "expected_output_true": sample["expected_output"],
            }
        )
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _report_markdown(metrics: Dict) -> str:
    first = metrics["metrics_by_generation"][0]
    final = metrics["metrics_by_generation"][-1]
    lines = [
        "# v0.5.9 BranchChain Toy Training Report",
        "",
        "This is a toy scaffold for BranchChain training shape correction. It is not a v0.5 release claim.",
        "",
        "## Summary",
        "",
        f"- dataset size: {metrics['dataset_size']}",
        f"- population size: {metrics['population_size']}",
        f"- generations: {metrics['generation_count']}",
        f"- generation 0 mean_reward: {first['mean_reward']}",
        f"- final mean_reward: {final['mean_reward']}",
        f"- generation 0 branch_path_accuracy: {first['branch_path_accuracy']}",
        f"- final branch_path_accuracy: {final['branch_path_accuracy']}",
        f"- generation 0 target_ir_accuracy: {first['target_ir_accuracy']}",
        f"- final target_ir_accuracy: {final['target_ir_accuracy']}",
        "",
        "## Curves",
        "",
        "- mean_reward: " + ", ".join(str(row["mean_reward"]) for row in metrics["metrics_by_generation"]),
        "- branch_path_accuracy: " + ", ".join(str(row["branch_path_accuracy"]) for row in metrics["metrics_by_generation"]),
        "- target_ir_accuracy: " + ", ".join(str(row["target_ir_accuracy"]) for row in metrics["metrics_by_generation"]),
        "",
        "## Most Common Wrong Branch Decisions",
        "",
    ]
    for label, count in final["most_common_wrong_branch_decisions"]:
        lines.append(f"- {label}: {count}")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not prove AGI.",
            "- This does not prove Transformer replacement.",
            "- This does not prove hardware BPU implementation.",
            "- This does not prove general program synthesis.",
            "- This does not train C source text.",
            "- This is a training-shape correction from flat classifier to branch-chain routing.",
        ]
    )
    return "\n".join(lines) + "\n"

