import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from jianmu.self_learning.arithmetic_targetir.expression_oracle import (
    UnsupportedReason,
    extract_expression_text,
    parse_controlled_expression,
)
from jianmu.self_learning.arithmetic_targetir.features import extract_arithmetic_features, feature_summary
from jianmu.self_learning.arithmetic_targetir.hashed_perceptron import HashedLabeledSample, HashedPerceptron
from jianmu.self_learning.arithmetic_targetir.target_ir import ArithmeticNode, ArithmeticTargetIR


STRUCTURE_LABELS = [
    "ADD_REDUCE",
    "ADD_THEN_MUL",
    "BIN_ADD",
    "BIN_DIV",
    "BIN_MUL",
    "BIN_SUB",
    "MUL_THEN_ADD",
    "PAREN_ADD_THEN_MUL",
    "PAREN_SUB_THEN_DIV",
    "SUB_THEN_MUL",
    "UNSUPPORTED",
]


@dataclass
class ExtractedSlots:
    numbers: List[int]
    operators: List[str]
    has_parentheses: bool
    expression_text: str

    def to_dict(self) -> Dict:
        return {
            "numbers": self.numbers,
            "operators": self.operators,
            "has_parentheses": self.has_parentheses,
            "expression_text": self.expression_text,
        }


@dataclass
class TargetIRPrediction:
    supported_pred: str
    expression_form_pred: str
    structure_label_pred: str
    extracted_slots: Dict
    target_ir_pred: Optional[ArithmeticTargetIR]
    unsupported_reason_pred: Optional[str]
    confidence_scores: Dict[str, Dict[str, float]]
    feature_summary: List[str]


class ArithmeticTargetIRRouter:
    def __init__(self, num_params: int = 1_048_576, epochs: int = 10, lr: float = 1.0, seed: int = 42):
        self.num_params = num_params
        self.head_params = max(1024, num_params // 3)
        self.epochs = epochs
        self.lr = lr
        self.seed = seed
        self.supported_head: Optional[HashedPerceptron] = None
        self.expression_form_head: Optional[HashedPerceptron] = None
        self.structure_head: Optional[HashedPerceptron] = None

    def fit(self, train_samples: List[Dict]):
        features_by_id = {
            sample["sample_id"]: extract_arithmetic_features(sample["input_text"])
            for sample in train_samples
        }
        supported_labels = ["supported", "unsupported"]
        form_labels = sorted({sample["expression_form"] for sample in train_samples})
        structure_labels = sorted({sample["structure_label"] for sample in train_samples} | set(STRUCTURE_LABELS))

        self.supported_head = HashedPerceptron(
            labels=supported_labels, num_params=self.head_params, epochs=self.epochs, lr=self.lr, seed=self.seed
        )
        self.expression_form_head = HashedPerceptron(
            labels=form_labels, num_params=self.head_params, epochs=self.epochs, lr=self.lr, seed=self.seed + 1
        )
        self.structure_head = HashedPerceptron(
            labels=structure_labels, num_params=self.head_params, epochs=self.epochs, lr=self.lr, seed=self.seed + 2
        )

        self.supported_head.fit(
            HashedLabeledSample(features_by_id[s["sample_id"]], "supported" if s["supported"] else "unsupported")
            for s in train_samples
        )
        self.expression_form_head.fit(
            HashedLabeledSample(features_by_id[s["sample_id"]], s["expression_form"])
            for s in train_samples
        )
        self.structure_head.fit(
            HashedLabeledSample(features_by_id[s["sample_id"]], s["structure_label"])
            for s in train_samples
        )
        return self

    def predict(self, input_text: str) -> TargetIRPrediction:
        self._ensure_fitted()
        features = extract_arithmetic_features(input_text)
        supported_pred = self.supported_head.predict(features)
        expression_form_pred = self.expression_form_head.predict(features)
        structure_label_pred = self.structure_head.predict(features)
        slots = extract_slots(input_text)

        unsupported_reason = None
        target_ir = None
        if supported_pred == "unsupported" or structure_label_pred == "UNSUPPORTED":
            unsupported_reason = _unsupported_reason_from_oracle(input_text) or "classifier_unsupported"
        else:
            try:
                target_ir = build_target_ir_from_structure(structure_label_pred, slots)
                target_ir.root.evaluate()
            except Exception as exc:
                unsupported_reason = f"invalid_targetir:{type(exc).__name__}"
                target_ir = None

        return TargetIRPrediction(
            supported_pred=supported_pred,
            expression_form_pred=expression_form_pred,
            structure_label_pred=structure_label_pred,
            extracted_slots=slots.to_dict(),
            target_ir_pred=target_ir,
            unsupported_reason_pred=unsupported_reason,
            confidence_scores={
                "supported": self.supported_head.scores(features),
                "expression_form": self.expression_form_head.scores(features),
                "structure": self.structure_head.scores(features),
            },
            feature_summary=feature_summary(features),
        )

    def save_json(self, path):
        self._ensure_fitted()
        base = Path(path)
        payload = {
            "num_params": self.num_params,
            "head_params": self.head_params,
            "epochs": self.epochs,
            "lr": self.lr,
            "seed": self.seed,
            "supported_head": _head_payload(self.supported_head),
            "expression_form_head": _head_payload(self.expression_form_head),
            "structure_head": _head_payload(self.structure_head),
        }
        base.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load_json(cls, path):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        router = cls(
            num_params=payload["num_params"],
            epochs=payload.get("epochs", 10),
            lr=payload.get("lr", 1.0),
            seed=payload.get("seed", 42),
        )
        router.head_params = payload.get("head_params", max(1024, router.num_params // 3))
        router.supported_head = _load_head(payload["supported_head"])
        router.expression_form_head = _load_head(payload["expression_form_head"])
        router.structure_head = _load_head(payload["structure_head"])
        return router

    def _ensure_fitted(self):
        if not (self.supported_head and self.expression_form_head and self.structure_head):
            raise RuntimeError("ArithmeticTargetIRRouter is not fitted")


def extract_slots(input_text: str) -> ExtractedSlots:
    expr = extract_expression_text(input_text)
    parsed = parse_controlled_expression(input_text)
    numbers: List[int] = []
    operators: List[str] = []
    if isinstance(parsed, ArithmeticTargetIR):
        for token in parsed.program_ir_tokens():
            if token["type"] == "LITERAL_INT":
                numbers.append(token["value"])
            else:
                operators.append(token["type"])
    return ExtractedSlots(
        numbers=numbers,
        operators=operators,
        has_parentheses="(" in expr or "（" in input_text,
        expression_text=expr,
    )


def build_target_ir_from_structure(label: str, slots: ExtractedSlots) -> ArithmeticTargetIR:
    numbers = slots.numbers
    if label == "UNSUPPORTED":
        raise ValueError("unsupported structure")
    if label == "ADD_REDUCE":
        if len(numbers) < 2:
            raise ValueError("ADD_REDUCE needs at least two numbers")
        node = ArithmeticNode.literal(numbers[0])
        for value in numbers[1:]:
            node = ArithmeticNode.op("add", node, ArithmeticNode.literal(value))
        return ArithmeticTargetIR(root=node, source_mode="regenerated_target")
    if len(numbers) < 2:
        raise ValueError(f"{label} needs at least two numbers")
    a = ArithmeticNode.literal(numbers[0])
    b = ArithmeticNode.literal(numbers[1])
    c = ArithmeticNode.literal(numbers[2]) if len(numbers) >= 3 else None
    if label == "BIN_ADD":
        node = ArithmeticNode.op("add", a, b)
    elif label == "BIN_SUB":
        node = ArithmeticNode.op("sub", a, b)
    elif label == "BIN_MUL":
        node = ArithmeticNode.op("mul", a, b)
    elif label == "BIN_DIV":
        node = ArithmeticNode.op("div", a, b)
    elif label == "ADD_THEN_MUL" and c is not None:
        node = ArithmeticNode.op("add", a, ArithmeticNode.op("mul", b, c))
    elif label == "MUL_THEN_ADD" and c is not None:
        node = ArithmeticNode.op("add", ArithmeticNode.op("mul", a, b), c)
    elif label == "SUB_THEN_MUL" and c is not None:
        node = ArithmeticNode.op("sub", a, ArithmeticNode.op("mul", b, c))
    elif label == "PAREN_ADD_THEN_MUL" and c is not None:
        node = ArithmeticNode.op("mul", ArithmeticNode.op("add", a, b), c)
    elif label == "PAREN_SUB_THEN_DIV" and c is not None:
        node = ArithmeticNode.op("div", ArithmeticNode.op("sub", a, b), c)
    else:
        raise ValueError(f"cannot build TargetIR for {label}")
    return ArithmeticTargetIR(root=node, source_mode="regenerated_target")


def _unsupported_reason_from_oracle(input_text: str) -> Optional[str]:
    parsed = parse_controlled_expression(input_text)
    if isinstance(parsed, UnsupportedReason):
        return parsed.reason
    return None


def _head_payload(head: HashedPerceptron) -> Dict:
    return {
        "labels": head.labels,
        "num_params": head.num_params,
        "epochs": head.epochs,
        "lr": head.lr,
        "seed": head.seed,
        "bias": head.bias,
        "nonzero_weights": {str(i): value for i, value in enumerate(head.weights) if value},
    }


def _load_head(payload: Dict) -> HashedPerceptron:
    weights = [0.0] * payload["num_params"]
    for key, value in payload.get("nonzero_weights", {}).items():
        weights[int(key)] = float(value)
    return HashedPerceptron(
        labels=payload["labels"],
        num_params=payload["num_params"],
        epochs=payload.get("epochs", 10),
        lr=payload.get("lr", 1.0),
        seed=payload.get("seed", 42),
        weights=weights,
        bias=payload.get("bias", {}),
    )

