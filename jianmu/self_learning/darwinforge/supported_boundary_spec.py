from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class SupportedBoundarySpec:
    version: str = "v0.8.4"
    supported_languages: List[str] = field(default_factory=lambda: ["zh", "math_expression", "mixed_zh_arabic"])
    supported_input_forms: List[str] = field(
        default_factory=lambda: [
            "zh_natural_arithmetic_request",
            "zh_technical_mixed_arithmetic_request",
            "explicit_c_arithmetic_like_supported_form",
            "implicit_c_arithmetic_like_supported_form",
            "math_expression",
            "zh_number_expression",
        ]
    )
    supported_arithmetic_families: List[str] = field(
        default_factory=lambda: ["addition", "subtraction", "multiplication", "exact_division", "mixed_precedence", "literal_only"]
    )
    supported_operators: List[str] = field(default_factory=lambda: ["+", "-", "*", "/", "parentheses", "mixed_precedence"])
    supported_number_forms: List[str] = field(default_factory=lambda: ["arabic_integer", "zh_integer", "signed_integer"])
    unsupported_current_but_future: List[str] = field(
        default_factory=lambda: [
            "english_arithmetic",
            "decimal_arithmetic",
            "variable_expressions",
            "equation_solving",
            "non_exact_division",
            "complex_multi_step_word_problem",
            "code_generation_beyond_arithmetic_target",
        ]
    )
    hard_reject_categories: List[str] = field(
        default_factory=lambda: [
            "poetry",
            "image_generation",
            "unrelated_request",
            "pure_chat",
            "http_server_request",
            "non_programming_instruction",
            "malicious_or_unsafe_request",
            "malformed_expression_without_arithmetic_intent",
        ]
    )

    def to_dict(self) -> Dict:
        return {
            "version": self.version,
            "supported_languages": self.supported_languages,
            "supported_input_forms": self.supported_input_forms,
            "supported_arithmetic_families": self.supported_arithmetic_families,
            "supported_operators": self.supported_operators,
            "supported_number_forms": self.supported_number_forms,
            "unsupported_current_but_future": self.unsupported_current_but_future,
            "hard_reject_categories": self.hard_reject_categories,
        }


@dataclass(frozen=True)
class BoundaryDecision:
    boundary_label: str
    reason: str
    confidence: float
    recommended_action: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def default_supported_boundary_spec() -> SupportedBoundarySpec:
    return SupportedBoundarySpec()


def classify_against_supported_boundary(sample: Dict, raw_text: str, canonical_text: str, metadata: Dict | None = None) -> BoundaryDecision:
    metadata = metadata or {}
    raw = raw_text or ""
    canonical = canonical_text or raw
    lowered = raw.lower()
    ood_class = metadata.get("ood_class") or sample.get("ood_class") or sample.get("input_mode") or ""

    if metadata.get("unsupported_reason") == "label_too_strict" or sample.get("unsupported_reason") == "label_too_strict":
        return BoundaryDecision("label_review_needed", "metadata marks this sample as needing label review", 0.8, "label_review_needed")

    if _is_hard_reject(raw, lowered, ood_class):
        return BoundaryDecision("hard_reject", "outside current arithmetic and compiler-verifiable scope", 0.9, "reject_guard_needed")

    if _is_future_domain(raw, canonical, lowered, ood_class):
        return BoundaryDecision("future_domain_candidate", "has computational intent but is outside the current supported boundary", 0.82, "future_domain")

    if _is_current_supported(raw, canonical, lowered, ood_class):
        if metadata.get("was_marked_ood") or sample.get("split") == "ood":
            return BoundaryDecision("near_supported_candidate", "near current supported arithmetic but still requires boundary review", 0.72, "candidate_for_supported_expansion")
        return BoundaryDecision("supported", "inside current supported arithmetic boundary", 0.88, "keep_supported")

    if _has_arithmetic_intent(raw, lowered) or _has_arithmetic_signal(canonical):
        return BoundaryDecision("near_supported_candidate", "arithmetic intent is nearby but boundary is not yet accepted", 0.62, "candidate_for_supported_expansion")

    return BoundaryDecision("unknown", "insufficient information to classify boundary", 0.2, "unknown")


def _is_hard_reject(raw: str, lowered: str, ood_class: str) -> bool:
    hard_classes = {"ood_unrelated_request", "instruction_not_programming", "malformed_expression"}
    hard_cues = ["诗", "画", "图片", "聊天", "http", "server", "poem", "image", "weather", "news"]
    return ood_class in hard_classes or any(cue in raw or cue in lowered for cue in hard_cues)


def _is_future_domain(raw: str, canonical: str, lowered: str, ood_class: str) -> bool:
    if ood_class in {"division_by_zero", "non_exact_division", "unsupported_operator", "unsupported_depth", "unsupported_arithmetic"}:
        return True
    if any(cue in lowered for cue in ["calculate", "plus", "minus", "times", "divide"]):
        return True
    if any(ch in canonical for ch in [".", "^", "="]):
        return True
    return False


def _is_current_supported(raw: str, canonical: str, lowered: str, ood_class: str) -> bool:
    if ood_class in {"ood_english_sentence", "ood_unrelated_request"}:
        return False
    return _has_arithmetic_signal(canonical) and (_has_zh(raw) or _looks_like_expression(canonical))


def _has_arithmetic_signal(text: str) -> bool:
    return any(ch.isdigit() for ch in text) and any(op in text for op in ["+", "-", "*", "/"])


def _has_arithmetic_intent(raw: str, lowered: str) -> bool:
    return any(cue in raw for cue in ["算", "计算", "输出", "加", "减", "乘", "除"]) or any(
        cue in lowered for cue in ["calculate", "plus", "minus", "times", "divide"]
    )


def _has_zh(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _looks_like_expression(text: str) -> bool:
    compact = text.replace(" ", "")
    return bool(compact) and all(ch.isdigit() or ch in "+-*/()" for ch in compact)
