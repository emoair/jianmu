import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.self_learning.learned_router.evaluate import MODEL_PATH, REPORT_PATH, train_and_evaluate


def main():
    epochs = 20
    lr = 1.0
    seed = 42
    metrics = train_and_evaluate(epochs=epochs, lr=lr, seed=seed)
    print(f"train size: {metrics['train_count']}")
    print(f"eval size: {metrics['eval_count']}")
    print(f"route labels: {metrics['route_id_label_count']}")
    print(f"task_family labels: {metrics['task_family_label_count']}")
    print(f"majority route_id accuracy: {metrics['majority_route_id_accuracy']}")
    print(f"majority supported accuracy: {metrics['majority_supported_accuracy']}")
    print(f"learned route_id accuracy: {metrics['learned_route_id_accuracy']}")
    print(f"learned task_family accuracy: {metrics['learned_task_family_accuracy']}")
    print(f"learned supported accuracy: {metrics['learned_supported_accuracy']}")
    print(f"unsupported precision/recall/f1: {metrics['unsupported_precision']} / {metrics['unsupported_recall']} / {metrics['unsupported_f1']}")
    print(f"report path: {REPORT_PATH}")
    print(f"model path: {MODEL_PATH}")


if __name__ == "__main__":
    main()

