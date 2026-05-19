import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.learned_router.features import extract_features, summarize_features
from jianmu.self_learning.learned_router.perceptron import LabeledSample, MulticlassPerceptron


@dataclass
class RoutePrediction:
    route_id: str
    task_family: str
    supported: str
    route_scores: Dict[str, float]
    task_family_scores: Dict[str, float]
    supported_scores: Dict[str, float]
    features_summary: Dict[str, float]


class RouteClassifier:
    def __init__(self, epochs: int = 20, lr: float = 1.0, seed: int = 42, ngram_range=(1, 3)):
        self.epochs = epochs
        self.lr = lr
        self.seed = seed
        self.ngram_range = tuple(ngram_range)
        self.route_model = None
        self.task_family_model = None
        self.supported_model = None

    def fit(self, train_samples: List[Dict]):
        route_labels = sorted({sample["route_id"] for sample in train_samples})
        family_labels = sorted({sample["task_family"] for sample in train_samples})
        supported_labels = ["supported", "unsupported"]

        route_training = []
        family_training = []
        supported_training = []
        for sample in train_samples:
            features = extract_features(sample["input_text"], self.ngram_range)
            route_training.append(LabeledSample(features, sample["route_id"]))
            family_training.append(LabeledSample(features, sample["task_family"]))
            supported_training.append(LabeledSample(features, _supported_label(sample)))

        self.route_model = MulticlassPerceptron(route_labels, self.epochs, self.lr, self.seed).fit(route_training)
        self.task_family_model = MulticlassPerceptron(family_labels, self.epochs, self.lr, self.seed).fit(family_training)
        self.supported_model = MulticlassPerceptron(supported_labels, self.epochs, self.lr, self.seed).fit(supported_training)
        return self

    def predict(self, input_text: str) -> RoutePrediction:
        features = extract_features(input_text, self.ngram_range)
        route_scores = self.route_model.scores(features)
        family_scores = self.task_family_model.scores(features)
        supported_scores = self.supported_model.scores(features)
        return RoutePrediction(
            route_id=self.route_model.predict(features),
            task_family=self.task_family_model.predict(features),
            supported=self.supported_model.predict(features),
            route_scores=route_scores,
            task_family_scores=family_scores,
            supported_scores=supported_scores,
            features_summary=summarize_features(features),
        )

    def save_json(self, path):
        payload = {
            "epochs": self.epochs,
            "lr": self.lr,
            "seed": self.seed,
            "ngram_range": list(self.ngram_range),
            "route_model": _model_payload(self.route_model),
            "task_family_model": _model_payload(self.task_family_model),
            "supported_model": _model_payload(self.supported_model),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load_json(cls, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        classifier = cls(
            epochs=payload.get("epochs", 20),
            lr=payload.get("lr", 1.0),
            seed=payload.get("seed", 42),
            ngram_range=tuple(payload.get("ngram_range", [1, 3])),
        )
        classifier.route_model = _model_from_payload(payload["route_model"])
        classifier.task_family_model = _model_from_payload(payload["task_family_model"])
        classifier.supported_model = _model_from_payload(payload["supported_model"])
        return classifier


def _supported_label(sample: Dict) -> str:
    return "supported" if sample["supported"] else "unsupported"


def _model_payload(model: MulticlassPerceptron) -> Dict:
    return {
        "labels": model.labels,
        "epochs": model.epochs,
        "lr": model.lr,
        "seed": model.seed,
        "weights": model.weights,
        "bias": model.bias,
    }


def _model_from_payload(payload: Dict) -> MulticlassPerceptron:
    return MulticlassPerceptron(
        labels=payload["labels"],
        epochs=payload.get("epochs", 20),
        lr=payload.get("lr", 1.0),
        seed=payload.get("seed", 42),
        weights=payload.get("weights", {}),
        bias=payload.get("bias", {}),
    )

