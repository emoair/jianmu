from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class CanonicalizationConfig:
    enabled: bool = True
    preserve_raw_text: bool = True
    expose_canonical_features: bool = True
    fail_open: bool = True


@dataclass(frozen=True)
class CanonicalToken:
    raw: str
    canonical: str
    token_type: str
    span: Tuple[int, int]
    confidence: float = 1.0

    def to_dict(self) -> Dict:
        return {
            "raw": self.raw,
            "canonical": self.canonical,
            "type": self.token_type,
            "span": list(self.span),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class CanonicalizationResult:
    raw_text: str
    canonical_text: str
    tokens: List[CanonicalToken]
    source_map: List[Dict]
    changed: bool
    warnings: List[str]

    def to_dict(self) -> Dict:
        return {
            "raw_text": self.raw_text,
            "canonical_text": self.canonical_text,
            "tokens": [token.to_dict() for token in self.tokens],
            "source_map": self.source_map,
            "changed": self.changed,
            "warnings": list(self.warnings),
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
}

OPERATOR_WORDS = [
    ("除以", "/", "OP_DIV"),
    ("加上", "+", "OP_PLUS"),
    ("减去", "-", "OP_MINUS"),
    ("乘以", "*", "OP_MUL"),
    ("加", "+", "OP_PLUS"),
    ("减", "-", "OP_MINUS"),
    ("乘", "*", "OP_MUL"),
    ("除", "/", "OP_DIV"),
]

FILLER_WORDS = [
    "等于多少",
    "是多少",
    "的结果",
    "请",
    "计算",
    "输出",
    "打印",
    "求",
    "结果",
    "值",
]


def canonicalize_symbols(text: str) -> CanonicalizationResult:
    """Canonical Symbol Layer（规范符号层）: raw text -> canonical text and source map only."""
    raw_text = text
    cleaned_text, suffix_warnings = _strip_dataset_artifact_suffix(raw_text)
    working, rewrite_tokens, warnings = _rewrite_parenthesis_phrase(cleaned_text)
    warnings = suffix_warnings + warnings
    tokens: List[CanonicalToken] = list(rewrite_tokens)
    canonical_parts: List[str] = []
    index = 0
    while index < len(working):
        ch = working[index]
        if ch.isspace() or ch in "，、,":
            index += 1
            continue
        if ch == "(":
            token = CanonicalToken(ch, "(", "LPAREN", (index, index + 1))
            tokens.append(token)
            canonical_parts.append(token.canonical)
            index += 1
            continue
        if ch == ")":
            token = CanonicalToken(ch, ")", "RPAREN", (index, index + 1))
            tokens.append(token)
            canonical_parts.append(token.canonical)
            index += 1
            continue
        if ch in "+-*/":
            token_type = {"+": "OP_PLUS", "-": "OP_MINUS", "*": "OP_MUL", "/": "OP_DIV"}[ch]
            token = CanonicalToken(ch, ch, token_type, (index, index + 1))
            tokens.append(token)
            canonical_parts.append(token.canonical)
            index += 1
            continue
        number_match = re.match(r"-?\d+", working[index:])
        if number_match:
            raw = number_match.group(0)
            token = CanonicalToken(raw, raw, "NUM", (index, index + len(raw)))
            tokens.append(token)
            canonical_parts.append(token.canonical)
            index += len(raw)
            continue
        matched = _match_operator(working, index)
        if matched:
            raw, canonical, token_type = matched
            token = CanonicalToken(raw, canonical, token_type, (index, index + len(raw)))
            tokens.append(token)
            canonical_parts.append(token.canonical)
            index += len(raw)
            continue
        number = _match_chinese_number(working, index)
        if number:
            raw, value = number
            token = CanonicalToken(raw, str(value), "NUM", (index, index + len(raw)))
            tokens.append(token)
            canonical_parts.append(token.canonical)
            index += len(raw)
            continue
        filler = _match_filler(working, index)
        if filler:
            tokens.append(CanonicalToken(filler, "", "TEXT", (index, index + len(filler))))
            index += len(filler)
            continue
        tokens.append(CanonicalToken(ch, ch, "TEXT", (index, index + 1), confidence=0.5))
        canonical_parts.append(ch)
        index += 1
    canonical_text = "".join(canonical_parts)
    source_map = [token.to_dict() for token in tokens if token.token_type != "TEXT" or token.canonical]
    return CanonicalizationResult(
        raw_text=raw_text,
        canonical_text=canonical_text,
        tokens=tokens,
        source_map=source_map,
        changed=canonical_text != raw_text.strip(),
        warnings=warnings,
    )


def _strip_dataset_artifact_suffix(text: str) -> Tuple[str, List[str]]:
    match = re.search(r"\s*(?:（|\()jm-v070-[^)）]+(?:）|\))\s*$", text)
    if not match:
        return text, []
    return text[: match.start()], ["stripped_dataset_artifact_suffix"]


def _rewrite_parenthesis_phrase(text: str) -> Tuple[str, List[CanonicalToken], List[str]]:
    normalized = text.replace("（", "(").replace("）", ")")
    warnings: List[str] = []
    tokens: List[CanonicalToken] = []
    match = re.fullmatch(r"(?:括号里|括号内)(.+?)再(乘以|乘|加上|加|减去|减|除以|除)(.+)", normalized)
    if match:
        inner, op, rest = match.groups()
        return f"({inner}){op}{rest}", tokens, warnings
    match = re.search(r"括号里(.+)", normalized)
    if match:
        warnings.append("unclosed_parenthesis_phrase")
    return normalized, tokens, warnings


def _match_operator(text: str, index: int):
    for raw, canonical, token_type in OPERATOR_WORDS:
        if text.startswith(raw, index):
            return raw, canonical, token_type
    return None


def _match_filler(text: str, index: int):
    for word in FILLER_WORDS:
        if text.startswith(word, index):
            return word
    return None


def _match_chinese_number(text: str, index: int):
    candidates = _number_candidates()
    for raw, value in candidates:
        if text.startswith(raw, index):
            return raw, value
    return None


def _number_candidates():
    values: Dict[str, int] = {}
    for raw, value in CHINESE_DIGITS.items():
        values[raw] = value
    values["十"] = 10
    for value in range(11, 20):
        values[f"十{_digit_to_zh(value - 10)}"] = value
    for tens in range(2, 6):
        values[f"{_digit_to_zh(tens)}十"] = tens * 10
        for ones in range(1, 10):
            value = tens * 10 + ones
            if value <= 50:
                values[f"{_digit_to_zh(tens)}十{_digit_to_zh(ones)}"] = value
    for value in range(1, 21):
        zh = _int_to_zh(value)
        values[f"负{zh}"] = -value
    return sorted(values.items(), key=lambda item: len(item[0]), reverse=True)


def _digit_to_zh(value: int) -> str:
    for raw, digit in CHINESE_DIGITS.items():
        if digit == value and raw != "两":
            return raw
    raise ValueError(value)


def _int_to_zh(value: int) -> str:
    if value < 10:
        return _digit_to_zh(value)
    if value == 10:
        return "十"
    if value < 20:
        return "十" + _digit_to_zh(value - 10)
    tens, ones = divmod(value, 10)
    if ones == 0:
        return _digit_to_zh(tens) + "十"
    return _digit_to_zh(tens) + "十" + _digit_to_zh(ones)
