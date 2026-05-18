import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NeuronResult:
    neuron_name: str
    score: float
    features: dict
    rationale: str


@dataclass
class SemanticFeatures:
    domain_scores: Dict[str, float] = field(default_factory=dict)
    operation_scores: Dict[str, float] = field(default_factory=dict)
    edit_intent_scores: Dict[str, float] = field(default_factory=dict)
    extracted_numbers: List[int] = field(default_factory=list)
    extracted_expression: Optional[str] = None
    expression_values: List[int] = field(default_factory=list)
    quantity: Optional[int] = None
    negated: bool = False
    has_previous_context: bool = False
    variable_focus: Optional[str] = None
    unsupported_language: bool = False
    unsupported_expression: bool = False
    neuron_results: List[NeuronResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "domain_scores": dict(self.domain_scores),
            "operation_scores": dict(self.operation_scores),
            "edit_intent_scores": dict(self.edit_intent_scores),
            "extracted_numbers": list(self.extracted_numbers),
            "extracted_expression": self.extracted_expression,
            "expression_values": list(self.expression_values),
            "quantity": self.quantity,
            "negated": self.negated,
            "has_previous_context": self.has_previous_context,
            "variable_focus": self.variable_focus,
            "unsupported_language": self.unsupported_language,
            "unsupported_expression": self.unsupported_expression,
        }


CHINESE_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_.])-?\d+")
NUMERIC_EXPRESSION_RE = re.compile(r"^\s*-?\d+(?:\s*\+\s*-?\d+)*\s*$")
UNSUPPORTED_NON_ADDITION_EXPRESSION_RE = re.compile(r"-?\d+\s*[-*/]\s*-?\d+")


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def is_unsupported_english_natural_language(text: str) -> bool:
    """English NL is out of scope; bare numeric expressions remain allowed."""
    if has_cjk(text):
        return False
    if NUMERIC_EXPRESSION_RE.match(text):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def has_unsupported_non_addition_expression(text: str) -> bool:
    """Reject binary -, *, / expressions in v0.5 without rejecting negative literals."""
    return bool(UNSUPPORTED_NON_ADDITION_EXPRESSION_RE.search(text))


def _score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _numbers_from_text(text: str) -> List[int]:
    return [int(m.group()) for m in NUMBER_RE.finditer(text)]


def _numbers_from_expression(expr: str) -> List[int]:
    return _numbers_from_text(expr)


def _has_any(text: str, tokens: List[str]) -> bool:
    lower = text.lower()
    return any(token.lower() in lower for token in tokens)


class SemanticNeuron:
    name = "SemanticNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        return NeuronResult(self.name, 0.0, {}, "inactive")


class NumberExtractorNeuron(SemanticNeuron):
    name = "NumberExtractorNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        nums = _numbers_from_text(text)
        return NeuronResult(
            self.name,
            _score(0.9 if nums else 0.0),
            {"numbers": nums},
            "digit literals with optional sign",
        )


class ChineseNumberNeuron(SemanticNeuron):
    name = "ChineseNumberNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        values = []
        for i, ch in enumerate(text):
            if ch not in CHINESE_DIGITS:
                continue
            next_ch = text[i + 1] if i + 1 < len(text) else ""
            # In phrases like "一个" or "两个", the numeral is quantity,
            # not the literal operand value.
            if next_ch in {"个", "位", "项"}:
                continue
            values.append(CHINESE_DIGITS[ch])
        return NeuronResult(
            self.name,
            _score(0.8 if values else 0.0),
            {"numbers": values},
            "Chinese numeral literals",
        )


class ExpressionExtractorNeuron(SemanticNeuron):
    name = "ExpressionExtractorNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        candidates = re.findall(r"-?\d+(?:\s*\+\s*-?\d+)+", text)
        if not candidates:
            return NeuronResult(self.name, 0.0, {}, "no explicit addition expression")
        expr = candidates[-1].replace(" ", "")
        return NeuronResult(
            self.name,
            0.95,
            {"expression": expr, "expression_values": _numbers_from_expression(expr)},
            "last explicit addition expression",
        )


class VariableExtractorNeuron(SemanticNeuron):
    name = "VariableExtractorNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        if _has_any(text, ["最后一个"]):
            return NeuronResult(self.name, 0.85, {"variable_focus": "last"}, "last operand focus")
        return NeuronResult(self.name, 0.0, {}, "no variable focus")


class NegationDetectorNeuron(SemanticNeuron):
    name = "NegationDetectorNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        negated = bool(re.search(r"不要|不用|禁止|保持不变|别(?:加|改|动|修改|变)", text))
        return NeuronResult(
            self.name,
            _score(0.95 if negated else 0.0),
            {"negated": negated},
            "negation cue before routing",
        )


class QuantityExtractorNeuron(SemanticNeuron):
    name = "QuantityExtractorNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        quantity = None
        m = re.search(r"(一个|一项)", text)
        if m:
            quantity = 1
        m = re.search(r"(两个|两项)", text)
        if m:
            quantity = 2
        for ch, value in CHINESE_DIGITS.items():
            if re.search(re.escape(ch) + r"(个|项|位)", text):
                quantity = value
                break
        m = re.search(r"(\d+)\s*(?:个|项|位)", text)
        if m:
            quantity = int(m.group(1))
        return NeuronResult(
            self.name,
            _score(0.85 if quantity is not None else 0.0),
            {"quantity": quantity},
            "operand quantity cue",
        )


class ArithmeticDomainNeuron(SemanticNeuron):
    name = "ArithmeticDomainNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = bool(features.extracted_numbers or features.extracted_expression)
        signal = signal or _has_any(text, ["加", "+", "和", "整数", "int"])
        return NeuronResult(self.name, _score(0.9 if signal else 0.1), {"domain": "arithmetic"}, "arithmetic cues")


class CodeEditDomainNeuron(SemanticNeuron):
    name = "CodeEditDomainNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = features.has_previous_context and _has_any(
            text, ["再", "多加", "改成", "换成", "保持", "变成"]
        )
        return NeuronResult(self.name, _score(0.9 if signal else 0.15), {"domain": "code_edit"}, "edit cues")


class CodeGenerateDomainNeuron(SemanticNeuron):
    name = "CodeGenerateDomainNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = _has_any(text, ["生成", "写", "定义", "输出", "C", "int", "printf", "main", "return"])
        signal = signal or (not features.has_previous_context and bool(features.extracted_numbers))
        return NeuronResult(self.name, _score(0.8 if signal else 0.2), {"domain": "code_generate"}, "generate cues")


class NoOpDomainNeuron(SemanticNeuron):
    name = "NoOpDomainNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = features.negated or _has_any(text, ["保持不变", "不变"])
        return NeuronResult(self.name, _score(0.95 if signal else 0.0), {"domain": "no_op"}, "keep/no-op cues")


class UnknownDomainNeuron(SemanticNeuron):
    name = "UnknownDomainNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        known = max(
            features.domain_scores.values(),
            default=0.0,
        )
        return NeuronResult(self.name, _score(1.0 - known), {"domain": "unknown"}, "residual domain score")


class AdditionNeuron(SemanticNeuron):
    name = "AdditionNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = _has_any(text, ["加", "+", "和"])
        return NeuronResult(self.name, _score(0.92 if signal else 0.25), {"operation": "addition"}, "addition cues")


class SubtractionNeuron(SemanticNeuron):
    name = "SubtractionNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = _has_any(text, ["减去"])
        return NeuronResult(self.name, _score(0.85 if signal else 0.0), {"operation": "subtraction"}, "subtraction cues")


class MultiplicationNeuron(SemanticNeuron):
    name = "MultiplicationNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = _has_any(text, ["乘", "*"])
        return NeuronResult(self.name, _score(0.85 if signal else 0.0), {"operation": "multiplication"}, "multiplication cues")


class DivisionNeuron(SemanticNeuron):
    name = "DivisionNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = _has_any(text, ["除", "/"])
        return NeuronResult(self.name, _score(0.85 if signal else 0.0), {"operation": "division"}, "division cues")


class MixedExpressionNeuron(SemanticNeuron):
    name = "MixedExpressionNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        ops = sum(1 for token in ["+", "-", "*", "/"] if token in text)
        return NeuronResult(
            self.name,
            _score(0.75 if ops > 1 else 0.0),
            {"operation": "mixed_expression"},
            "multiple operator cues",
        )


class AppendOperandNeuron(SemanticNeuron):
    name = "AppendOperandNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = features.has_previous_context and _has_any(text, ["再加", "多加"])
        score = 0.9 if signal and (features.quantity in (None, 1)) and not features.negated else 0.25
        return NeuronResult(self.name, _score(score), {"edit_intent": "append_operand"}, "single append vote")


class AppendMultipleOperandsNeuron(SemanticNeuron):
    name = "AppendMultipleOperandsNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = features.has_previous_context and (features.quantity or 0) > 1
        score = 0.92 if signal and _has_any(text, ["再加", "多加"]) and not features.negated else 0.0
        return NeuronResult(
            self.name,
            _score(score),
            {"edit_intent": "append_multiple_operands"},
            "multi-operand append vote",
        )


class ReplaceOperandNeuron(SemanticNeuron):
    name = "ReplaceOperandNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = features.has_previous_context and _has_any(text, ["改成", "换成", "替换"])
        score = 0.95 if signal and not features.negated else 0.15
        return NeuronResult(self.name, _score(score), {"edit_intent": "replace_operand"}, "replace vote")


class RewriteExpressionNeuron(SemanticNeuron):
    name = "RewriteExpressionNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = bool(features.extracted_expression) and _has_any(text, ["变成", "改成"])
        score = 0.96 if signal and not features.negated else 0.0
        return NeuronResult(self.name, _score(score), {"edit_intent": "rewrite_expression"}, "explicit expression rewrite vote")


class KeepExistingNeuron(SemanticNeuron):
    name = "KeepExistingNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = features.has_previous_context and (
            features.negated or _has_any(text, ["保持不变", "不变", "keep existing", "unchanged"])
        )
        return NeuronResult(self.name, _score(0.98 if signal else 0.0), {"edit_intent": "keep_existing"}, "no-op vote")


class GenerateNewNeuron(SemanticNeuron):
    name = "GenerateNewNeuron"

    def activate(self, text: str, features: SemanticFeatures) -> NeuronResult:
        signal = (not features.has_previous_context) or _has_any(text, ["生成", "写", "定义", "输出"])
        score = 0.85 if signal and not features.negated else 0.3
        return NeuronResult(self.name, _score(score), {"edit_intent": "generate_new"}, "fresh generation vote")
