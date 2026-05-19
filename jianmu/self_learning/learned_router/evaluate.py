import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.learned_router.route_classifier import RouteClassifier


TRAIN_PATH = Path("datasets") / "v0_5_6" / "jianmu_zh_intent_1000_train.jsonl"
EVAL_PATH = Path("datasets") / "v0_5_6" / "jianmu_zh_intent_1000_eval.jsonl"
RECORD_DIR = Path("records") / "v0_5_7"
METRICS_PATH = RECORD_DIR / "route_classifier_metrics.json"
REPORT_PATH = RECORD_DIR / "route_classifier_report.md"
PREDICTIONS_PATH = RECORD_DIR / "route_classifier_predictions_eval.jsonl"
MODEL_PATH = RECORD_DIR / "route_classifier_model.json"


def load_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def train_and_evaluate(
    train_path: Path = TRAIN_PATH,
    eval_path: Path = EVAL_PATH,
    output_dir: Path = RECORD_DIR,
    epochs: int = 20,
    lr: float = 1.0,
    seed: int = 42,
) -> Dict:
    train_samples = load_jsonl(train_path)
    eval_samples = load_jsonl(eval_path)
    classifier = RouteClassifier(epochs=epochs, lr=lr, seed=seed).fit(train_samples)

    majority = _majority_labels(train_samples)
    predictions = [_prediction_record(classifier, sample) for sample in eval_samples]
    learned_metrics = _metrics(eval_samples, predictions)
    majority_metrics = _majority_metrics(eval_samples, majority)
    metrics = {
        "train_count": len(train_samples),
        "eval_count": len(eval_samples),
        "route_id_label_count": len({sample["route_id"] for sample in train_samples}),
        "task_family_label_count": len({sample["task_family"] for sample in train_samples}),
        "majority_route_id_accuracy": majority_metrics["route_id_accuracy"],
        "majority_task_family_accuracy": majority_metrics["task_family_accuracy"],
        "majority_supported_accuracy": majority_metrics["supported_accuracy"],
        "learned_route_id_accuracy": learned_metrics["route_id_accuracy"],
        "learned_task_family_accuracy": learned_metrics["task_family_accuracy"],
        "learned_supported_accuracy": learned_metrics["supported_accuracy"],
        **learned_metrics,
        "majority_labels": majority,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    classifier.save_json(output_dir / MODEL_PATH.name)
    _write_json(output_dir / METRICS_PATH.name, metrics)
    _write_jsonl(output_dir / PREDICTIONS_PATH.name, predictions)
    (output_dir / REPORT_PATH.name).write_text(_build_report(metrics), encoding="utf-8")
    return metrics


def _prediction_record(classifier: RouteClassifier, sample: Dict) -> Dict:
    prediction = classifier.predict(sample["input_text"])
    top_route_scores = sorted(
        prediction.route_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:5]
    true_supported = bool(sample["supported"])
    pred_supported = prediction.supported == "supported"
    return {
        "sample_id": sample["sample_id"],
        "input_text": sample["input_text"],
        "true_route_id": sample["route_id"],
        "pred_route_id": prediction.route_id,
        "true_task_family": sample["task_family"],
        "pred_task_family": prediction.task_family,
        "true_supported": true_supported,
        "pred_supported": pred_supported,
        "correct_route": prediction.route_id == sample["route_id"],
        "correct_family": prediction.task_family == sample["task_family"],
        "correct_supported": pred_supported == true_supported,
        "top_route_scores": top_route_scores,
    }


def _metrics(eval_samples: List[Dict], predictions: List[Dict]) -> Dict:
    eval_count = len(eval_samples)
    route_correct = sum(1 for pred in predictions if pred["correct_route"])
    family_correct = sum(1 for pred in predictions if pred["correct_family"])
    supported_correct = sum(1 for pred in predictions if pred["correct_supported"])

    per_route_total = Counter(sample["route_id"] for sample in eval_samples)
    per_route_correct = Counter(pred["true_route_id"] for pred in predictions if pred["correct_route"])
    per_route_accuracy = {
        route_id: round(per_route_correct[route_id] / per_route_total[route_id], 4)
        for route_id in sorted(per_route_total)
    }
    macro_accuracy = round(sum(per_route_accuracy.values()) / max(1, len(per_route_accuracy)), 4)

    confusion = defaultdict(Counter)
    for pred in predictions:
        confusion[pred["true_route_id"]][pred["pred_route_id"]] += 1
    confusion_matrix = {
        true: dict(pred_counts)
        for true, pred_counts in sorted(confusion.items())
    }

    unsupported_tp = sum(
        1 for pred in predictions
        if pred["true_supported"] is False and pred["pred_supported"] is False
    )
    unsupported_fp = sum(
        1 for pred in predictions
        if pred["true_supported"] is True and pred["pred_supported"] is False
    )
    unsupported_fn = sum(
        1 for pred in predictions
        if pred["true_supported"] is False and pred["pred_supported"] is True
    )
    precision = unsupported_tp / max(1, unsupported_tp + unsupported_fp)
    recall = unsupported_tp / max(1, unsupported_tp + unsupported_fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)

    error_types = Counter(
        f"{pred['true_route_id']} -> {pred['pred_route_id']}"
        for pred in predictions
        if not pred["correct_route"]
    )
    return {
        "route_id_accuracy": round(route_correct / eval_count, 4),
        "task_family_accuracy": round(family_correct / eval_count, 4),
        "supported_accuracy": round(supported_correct / eval_count, 4),
        "macro_accuracy_by_route_id": macro_accuracy,
        "per_route_id_accuracy": per_route_accuracy,
        "confusion_matrix_route_id": confusion_matrix,
        "unsupported_precision": round(precision, 4),
        "unsupported_recall": round(recall, 4),
        "unsupported_f1": round(f1, 4),
        "most_common_errors": error_types.most_common(10),
    }


def _majority_labels(train_samples: List[Dict]) -> Dict[str, str]:
    return {
        "route_id": Counter(sample["route_id"] for sample in train_samples).most_common(1)[0][0],
        "task_family": Counter(sample["task_family"] for sample in train_samples).most_common(1)[0][0],
        "supported": Counter("supported" if sample["supported"] else "unsupported" for sample in train_samples).most_common(1)[0][0],
    }


def _majority_metrics(eval_samples: List[Dict], majority: Dict[str, str]) -> Dict[str, float]:
    count = len(eval_samples)
    return {
        "route_id_accuracy": round(sum(1 for sample in eval_samples if sample["route_id"] == majority["route_id"]) / count, 4),
        "task_family_accuracy": round(sum(1 for sample in eval_samples if sample["task_family"] == majority["task_family"]) / count, 4),
        "supported_accuracy": round(sum(1 for sample in eval_samples if ("supported" if sample["supported"] else "unsupported") == majority["supported"]) / count, 4),
    }


def _build_report(metrics: Dict) -> str:
    lines = [
        "# Tiny Learned Route Classifier Baseline",
        "",
        f"- train count: {metrics['train_count']}",
        f"- eval count: {metrics['eval_count']}",
        f"- route_id labels: {metrics['route_id_label_count']}",
        f"- task_family labels: {metrics['task_family_label_count']}",
        "",
        "## Majority Baseline",
        "",
        f"- majority_route_id_accuracy: {metrics['majority_route_id_accuracy']}",
        f"- majority_task_family_accuracy: {metrics['majority_task_family_accuracy']}",
        f"- majority_supported_accuracy: {metrics['majority_supported_accuracy']}",
        "",
        "## Learned Perceptron",
        "",
        f"- learned_route_id_accuracy: {metrics['learned_route_id_accuracy']}",
        f"- learned_task_family_accuracy: {metrics['learned_task_family_accuracy']}",
        f"- learned_supported_accuracy: {metrics['learned_supported_accuracy']}",
        f"- unsupported_precision: {metrics['unsupported_precision']}",
        f"- unsupported_recall: {metrics['unsupported_recall']}",
        f"- unsupported_f1: {metrics['unsupported_f1']}",
        "",
        "## Per Route Accuracy",
        "",
    ]
    for route_id, accuracy in metrics["per_route_id_accuracy"].items():
        lines.append(f"- {route_id}: {accuracy}")
    lines.extend([
        "",
        "## Most Common Route Errors",
        "",
    ])
    if metrics["most_common_errors"]:
        for error, count in metrics["most_common_errors"]:
            lines.append(f"- {error}: {count}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Non-Claims",
        "",
        "- This does not prove general learned routing.",
        "- This does not generate ProgramIR tokens yet.",
        "- This does not replace the compiler-validated backend.",
        "- This is only a tiny learned route classification baseline.",
        "",
    ])
    return "\n".join(lines)


def _write_json(path: Path, payload: Dict):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: List[Dict]):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    train_and_evaluate()

