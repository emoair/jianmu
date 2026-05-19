import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass
class HashedLabeledSample:
    features: Dict[str, float]
    label: str


@dataclass
class HashedPerceptron:
    labels: List[str]
    num_params: int = 1_048_576
    epochs: int = 10
    lr: float = 1.0
    seed: int = 42
    weights: List[float] = field(default_factory=list)
    bias: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.labels = sorted(self.labels)
        if not self.weights:
            self.weights = [0.0] * self.num_params
        if len(self.weights) != self.num_params:
            raise ValueError("weights length must match num_params")
        for label in self.labels:
            self.bias.setdefault(label, 0.0)

    def fit(self, samples: Iterable[HashedLabeledSample]):
        training = list(samples)
        rng = random.Random(self.seed)
        for _ in range(self.epochs):
            rng.shuffle(training)
            for sample in training:
                predicted = self.predict(sample.features)
                if predicted == sample.label:
                    continue
                self._update(sample.label, sample.features, self.lr)
                self._update(predicted, sample.features, -self.lr)
                self.bias[sample.label] += self.lr
                self.bias[predicted] -= self.lr
        return self

    def predict(self, features: Dict[str, float]) -> str:
        scores = self.scores(features)
        return max(self.labels, key=lambda label: (scores[label], label))

    def scores(self, features: Dict[str, float]) -> Dict[str, float]:
        return {label: self.score(label, features) for label in self.labels}

    def score(self, label: str, features: Dict[str, float]) -> float:
        total = self.bias.get(label, 0.0)
        for feature, value in features.items():
            total += self.weights[self.index(label, feature)] * value
        return total

    def index(self, label: str, feature: str) -> int:
        digest = hashlib.blake2b(f"{label}::{feature}".encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.num_params

    def save_json(self, path):
        nonzero = {str(i): value for i, value in enumerate(self.weights) if value}
        payload = {
            "labels": self.labels,
            "num_params": self.num_params,
            "epochs": self.epochs,
            "lr": self.lr,
            "seed": self.seed,
            "bias": self.bias,
            "nonzero_weights": nonzero,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load_json(cls, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        weights = [0.0] * payload["num_params"]
        for key, value in payload.get("nonzero_weights", {}).items():
            weights[int(key)] = float(value)
        return cls(
            labels=payload["labels"],
            num_params=payload["num_params"],
            epochs=payload.get("epochs", 10),
            lr=payload.get("lr", 1.0),
            seed=payload.get("seed", 42),
            weights=weights,
            bias=payload.get("bias", {}),
        )

    def _update(self, label: str, features: Dict[str, float], scale: float):
        for feature, value in features.items():
            self.weights[self.index(label, feature)] += scale * value

