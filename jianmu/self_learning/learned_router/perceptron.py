import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass
class LabeledSample:
    features: Dict[str, float]
    label: str


@dataclass
class MulticlassPerceptron:
    labels: List[str]
    epochs: int = 20
    lr: float = 1.0
    seed: int = 42
    weights: Dict[str, Dict[str, float]] = field(default_factory=dict)
    bias: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.labels = sorted(self.labels)
        for label in self.labels:
            self.weights.setdefault(label, {})
            self.bias.setdefault(label, 0.0)

    def fit(self, samples: Iterable[LabeledSample]):
        training = list(samples)
        rng = random.Random(self.seed)
        for _ in range(self.epochs):
            rng.shuffle(training)
            for sample in training:
                y_true = sample.label
                y_pred = self.predict(sample.features)
                if y_pred == y_true:
                    continue
                self._update(y_true, sample.features, self.lr)
                self._update(y_pred, sample.features, -self.lr)
                self.bias[y_true] += self.lr
                self.bias[y_pred] -= self.lr
        return self

    def predict(self, features: Dict[str, float]) -> str:
        scores = self.scores(features)
        return max(self.labels, key=lambda label: (scores[label], label))

    def scores(self, features: Dict[str, float]) -> Dict[str, float]:
        return {
            label: self.bias.get(label, 0.0) + sum(
                self.weights.get(label, {}).get(feature, 0.0) * value
                for feature, value in features.items()
            )
            for label in self.labels
        }

    def save_json(self, path):
        payload = {
            "labels": self.labels,
            "epochs": self.epochs,
            "lr": self.lr,
            "seed": self.seed,
            "weights": self.weights,
            "bias": self.bias,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load_json(cls, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            labels=payload["labels"],
            epochs=payload.get("epochs", 20),
            lr=payload.get("lr", 1.0),
            seed=payload.get("seed", 42),
            weights=payload.get("weights", {}),
            bias=payload.get("bias", {}),
        )

    def _update(self, label: str, features: Dict[str, float], scale: float):
        label_weights = self.weights.setdefault(label, {})
        for feature, value in features.items():
            label_weights[feature] = label_weights.get(feature, 0.0) + scale * value

