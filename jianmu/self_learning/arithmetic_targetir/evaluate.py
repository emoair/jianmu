import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from jianmu.sandbox import Sandbox
from jianmu.self_learning.arithmetic_targetir.dataset_generator import (
    EVAL_PATH,
    TRAIN_PATH,
    ensure_arithmetic_targetir_dataset,
)
from jianmu.self_learning.arithmetic_targetir.expression_oracle import UnsupportedReason, parse_controlled_expression
from jianmu.self_learning.arithmetic_targetir.targetir_router import ArithmeticTargetIRRouter


RECORD_DIR = Path("records/v0_5_8")
METRICS_PATH = RECORD_DIR / "arithmetic_targetir_metrics.json"
REPORT_PATH = RECORD_DIR / "arithmetic_targetir_report.md"
PREDICTIONS_PATH = RECORD_DIR / "arithmetic_targetir_predictions_eval.jsonl"
MODEL_PATH = RECORD_DIR / "arithmetic_targetir_model.json"


def train_and_evaluate(
    train_path=TRAIN_PATH,
    eval_path=EVAL_PATH,
    output_dir=RECORD_DIR,
    num_params: int = 1_048_576,
    epochs: int = 10,
    lr: float = 1.0,
    seed: int = 42,
    max_compile_checks: int = 100,
) -> Dict:
    train_path = Path(train_path)
    eval_path = Path(eval_path)
    if not train_path.exists() or not eval_path.exists():
        ensure_arithmetic_targetir_dataset()

    train_samples = _read_jsonl(train_path)
    eval_samples = _read_jsonl(eval_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    router = ArithmeticTargetIRRouter(num_params=num_params, epochs=epochs, lr=lr, seed=seed).fit(train_samples)
    predictions, metrics = evaluate_router(router, train_samples, eval_samples, max_compile_checks=max_compile_checks)

    model_path = output_dir / MODEL_PATH.name
    metrics_path = output_dir / METRICS_PATH.name
    report_path = output_dir / REPORT_PATH.name
    predictions_path = output_dir / PREDICTIONS_PATH.name
    router.save_json(model_path)
    metrics["model_path"] = str(model_path)
    metrics["report_path"] = str(report_path)
    metrics["predictions_path"] = str(predictions_path)
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    predictions_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in predictions),
        encoding="utf-8",
    )
    report_path.write_text(_build_report(metrics), encoding="utf-8")
    return metrics


def evaluate_router(
    router: ArithmeticTargetIRRouter,
    train_samples: List[Dict],
    eval_samples: List[Dict],
    max_compile_checks: int = 100,
) -> Tuple[List[Dict], Dict]:
    majority = _majority_baseline(train_samples)
    majority_counts = Counter()
    learned_counts = Counter()
    unsupported_counts = Counter()
    structure_wrong_but_target_correct = 0
    error_counter = Counter()
    per_structure_total = Counter()
    per_structure_correct = Counter()
    predictions: List[Dict] = []
    compile_checked = 0
    compile_success = 0
    run_success = 0
    sandbox_output_match = 0
    sandbox = Sandbox()

    oracle_correct = 0
    for sample in eval_samples:
        true_supported = bool(sample["supported"])
        true_supported_label = "supported" if true_supported else "unsupported"
        true_canonical = sample["target_ir"]["canonical"] if true_supported else None
        true_expected_output = sample["target_ir"]["expected_output"] if true_supported else None
        pred = router.predict(sample["input_text"])

        pred_supported_bool = pred.supported_pred == "supported" and pred.target_ir_pred is not None
        pred_canonical = pred.target_ir_pred.canonical_expr if pred.target_ir_pred else None
        pred_expected_output = pred.target_ir_pred.expected_output if pred.target_ir_pred else None
        correct_supported = (pred.supported_pred == true_supported_label) if not true_supported else pred_supported_bool
        correct_form = pred.expression_form_pred == sample["expression_form"]
        correct_structure = pred.structure_label_pred == sample["structure_label"]
        target_exact = true_supported and pred_canonical == true_canonical
        expected_match = true_supported and pred_expected_output == true_expected_output

        if target_exact and not correct_structure:
            structure_wrong_but_target_correct += 1
        if true_supported:
            per_structure_total[sample["structure_label"]] += 1
            if correct_structure:
                per_structure_correct[sample["structure_label"]] += 1
        if pred.structure_label_pred != sample["structure_label"]:
            error_counter[f"{sample['structure_label']} -> {pred.structure_label_pred}"] += 1

        _update_binary_counts(unsupported_counts, not true_supported, not pred_supported_bool)
        _update_majority_counts(majority_counts, sample, majority)
        learned_counts["supported_correct"] += int(correct_supported)
        learned_counts["form_correct"] += int(correct_form)
        learned_counts["structure_correct"] += int(correct_structure)
        learned_counts["target_exact"] += int(target_exact)
        learned_counts["expected_match"] += int(expected_match)
        learned_counts["task_success"] += int(target_exact and expected_match)

        compile_row = {"compile_checked": False, "compile_success": None, "run_success": None, "stdout": None}
        if pred.target_ir_pred and compile_checked < max_compile_checks:
            result = sandbox.run(pred.target_ir_pred.to_c_program())
            compile_checked += 1
            compile_success += int(result.compile_success)
            run_success += int(result.run_success)
            sandbox_output_match += int(result.run_success and result.stdout == pred_expected_output)
            compile_row = {
                "compile_checked": True,
                "compile_success": result.compile_success,
                "run_success": result.run_success,
                "stdout": result.stdout,
            }

        oracle_correct += int(_oracle_baseline_correct(sample))
        predictions.append(
            {
                "sample_id": sample["sample_id"],
                "input_text": sample["input_text"],
                "true_supported": true_supported,
                "pred_supported": pred_supported_bool,
                "true_expression_form": sample["expression_form"],
                "pred_expression_form": pred.expression_form_pred,
                "true_structure_label": sample["structure_label"],
                "pred_structure_label": pred.structure_label_pred,
                "true_target_ir": true_canonical,
                "pred_target_ir": pred_canonical,
                "correct_supported": correct_supported,
                "correct_expression_form": correct_form,
                "correct_structure": correct_structure,
                "target_ir_exact_match": target_exact,
                "expected_output_match": expected_match,
                "top_structure_scores": _top_scores(pred.confidence_scores["structure"]),
                **compile_row,
            }
        )

    total = len(eval_samples)
    unsupported_precision, unsupported_recall, unsupported_f1 = _precision_recall_f1(unsupported_counts)
    compile_denominator = max(compile_checked, 1)
    metrics = {
        "train_count": len(train_samples),
        "eval_count": total,
        "num_params": router.num_params,
        "head_params": router.head_params,
        "max_compile_checks": max_compile_checks,
        "compile_checked": compile_checked,
        "supported_accuracy": round(learned_counts["supported_correct"] / total, 4),
        "unsupported_precision": unsupported_precision,
        "unsupported_recall": unsupported_recall,
        "unsupported_f1": unsupported_f1,
        "expression_form_accuracy": round(learned_counts["form_correct"] / total, 4),
        "structure_label_accuracy": round(learned_counts["structure_correct"] / total, 4),
        "target_ir_exact_match": round(learned_counts["target_exact"] / total, 4),
        "expected_output_match": round(learned_counts["expected_match"] / total, 4),
        "compile_success_rate": round(compile_success / compile_denominator, 4),
        "run_success_rate": round(run_success / compile_denominator, 4),
        "sandbox_output_match_rate": round(sandbox_output_match / compile_denominator, 4),
        "task_success_rate": round(learned_counts["task_success"] / total, 4),
        "majority_supported_accuracy": round(majority_counts["supported_correct"] / total, 4),
        "majority_expression_form_accuracy": round(majority_counts["form_correct"] / total, 4),
        "majority_structure_label_accuracy": round(majority_counts["structure_correct"] / total, 4),
        "oracle_parser_upper_bound": round(oracle_correct / total, 4),
        "structure_wrong_but_target_correct": structure_wrong_but_target_correct,
        "structure_label_count": len({s["structure_label"] for s in train_samples}),
        "expression_form_label_count": len({s["expression_form"] for s in train_samples}),
        "majority_labels": majority,
        "per_structure_accuracy": {
            label: round(per_structure_correct[label] / count, 4)
            for label, count in sorted(per_structure_total.items())
        },
        "most_common_errors": error_counter.most_common(10),
    }
    return predictions, metrics


def _read_jsonl(path: Path) -> List[Dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _majority_baseline(train_samples: List[Dict]) -> Dict[str, str]:
    return {
        "supported": Counter("supported" if s["supported"] else "unsupported" for s in train_samples).most_common(1)[0][0],
        "expression_form": Counter(s["expression_form"] for s in train_samples).most_common(1)[0][0],
        "structure_label": Counter(s["structure_label"] for s in train_samples).most_common(1)[0][0],
    }


def _update_majority_counts(counts: Counter, sample: Dict, majority: Dict[str, str]):
    counts["supported_correct"] += int(majority["supported"] == ("supported" if sample["supported"] else "unsupported"))
    counts["form_correct"] += int(majority["expression_form"] == sample["expression_form"])
    counts["structure_correct"] += int(majority["structure_label"] == sample["structure_label"])


def _update_binary_counts(counts: Counter, true_unsupported: bool, pred_unsupported: bool):
    if true_unsupported and pred_unsupported:
        counts["tp"] += 1
    elif not true_unsupported and pred_unsupported:
        counts["fp"] += 1
    elif true_unsupported and not pred_unsupported:
        counts["fn"] += 1
    else:
        counts["tn"] += 1


def _precision_recall_f1(counts: Counter):
    precision = counts["tp"] / max(counts["tp"] + counts["fp"], 1)
    recall = counts["tp"] / max(counts["tp"] + counts["fn"], 1)
    f1 = (2 * precision * recall / max(precision + recall, 1e-12)) if precision or recall else 0.0
    return round(precision, 4), round(recall, 4), round(f1, 4)


def _oracle_baseline_correct(sample: Dict) -> bool:
    parsed = parse_controlled_expression(sample["input_text"])
    if isinstance(parsed, UnsupportedReason):
        return not sample["supported"]
    return bool(sample["supported"]) and parsed.canonical_expr == sample["target_ir"]["canonical"]


def _top_scores(scores: Dict[str, float], limit: int = 5):
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]


def _build_report(metrics: Dict) -> str:
    lines = [
        "# v0.5.8 1M Arithmetic TargetIR Router Baseline",
        "",
        "This is a development experiment, not a v0.5 release claim.",
        "",
        "## Dataset",
        "",
        f"- train: {metrics['train_count']}",
        f"- eval: {metrics['eval_count']}",
        f"- configured parameter budget: {metrics['num_params']}",
        f"- hash table params per head: {metrics['head_params']}",
        f"- compiler sandbox checks: {metrics['compile_checked']}",
        "",
        "## Baselines",
        "",
        f"- majority_supported_accuracy: {metrics['majority_supported_accuracy']}",
        f"- majority_expression_form_accuracy: {metrics['majority_expression_form_accuracy']}",
        f"- majority_structure_label_accuracy: {metrics['majority_structure_label_accuracy']}",
        f"- oracle_parser_upper_bound: {metrics['oracle_parser_upper_bound']}",
        "",
        "The oracle parser is the labeling oracle and deterministic upper bound. The learned router is evaluated as a routing/structure classifier, not as a parser replacement yet.",
        "",
        "## Learned Router Metrics",
        "",
        f"- supported_accuracy: {metrics['supported_accuracy']}",
        f"- unsupported_precision: {metrics['unsupported_precision']}",
        f"- unsupported_recall: {metrics['unsupported_recall']}",
        f"- unsupported_f1: {metrics['unsupported_f1']}",
        f"- expression_form_accuracy: {metrics['expression_form_accuracy']}",
        f"- structure_label_accuracy: {metrics['structure_label_accuracy']}",
        f"- target_ir_exact_match: {metrics['target_ir_exact_match']}",
        f"- expected_output_match: {metrics['expected_output_match']}",
        f"- compile_success_rate: {metrics['compile_success_rate']}",
        f"- run_success_rate: {metrics['run_success_rate']}",
        f"- task_success_rate: {metrics['task_success_rate']}",
        f"- structure_wrong_but_target_correct: {metrics['structure_wrong_but_target_correct']}",
        "",
        "## Most Common Structure Errors",
        "",
    ]
    for label, count in metrics["most_common_errors"]:
        lines.append(f"- {label}: {count}")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- This does not prove general program generation.",
            "- This does not train or emit C source text directly.",
            "- This does not patch old C source text.",
            "- This does not replace the compiler-validated backend.",
            "- This does not prove AGI, Transformer replacement, or hardware BPU implementation.",
        ]
    )
    return "\n".join(lines) + "\n"

