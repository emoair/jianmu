import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jianmu.self_learning.arithmetic_targetir.dataset_generator import ensure_arithmetic_targetir_dataset
from jianmu.self_learning.arithmetic_targetir.evaluate import train_and_evaluate


def main():
    train, eval_samples = ensure_arithmetic_targetir_dataset()
    metrics = train_and_evaluate(
        num_params=1_048_576,
        epochs=10,
        lr=1.0,
        seed=42,
        max_compile_checks=100,
    )
    print(f"train size: {len(train)}")
    print(f"eval size: {len(eval_samples)}")
    print(f"num_params: {metrics['num_params']}")
    print(f"expression form labels: {metrics['expression_form_label_count']}")
    print(f"structure labels: {metrics['structure_label_count']}")
    print(f"majority supported accuracy: {metrics['majority_supported_accuracy']}")
    print(f"majority structure accuracy: {metrics['majority_structure_label_accuracy']}")
    print(f"oracle parser upper bound: {metrics['oracle_parser_upper_bound']}")
    print(f"supported accuracy: {metrics['supported_accuracy']}")
    print(f"unsupported precision/recall/f1: {metrics['unsupported_precision']} / {metrics['unsupported_recall']} / {metrics['unsupported_f1']}")
    print(f"expression_form_accuracy: {metrics['expression_form_accuracy']}")
    print(f"structure_label_accuracy: {metrics['structure_label_accuracy']}")
    print(f"target_ir_exact_match: {metrics['target_ir_exact_match']}")
    print(f"expected_output_match: {metrics['expected_output_match']}")
    print(f"compile_success_rate: {metrics['compile_success_rate']}")
    print(f"run_success_rate: {metrics['run_success_rate']}")
    print(f"task_success_rate: {metrics['task_success_rate']}")
    print(f"report path: {metrics['report_path']}")
    print(f"model path: {metrics['model_path']}")


if __name__ == "__main__":
    main()

