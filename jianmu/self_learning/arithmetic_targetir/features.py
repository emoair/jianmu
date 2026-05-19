import re
from typing import Dict, List

from jianmu.self_learning.arithmetic_targetir.expression_oracle import (
    CHINESE_DIGITS,
    UnsupportedReason,
    extract_expression_text,
    parse_controlled_expression,
    tokenize_expression,
)


KEYWORDS = [
    "写一个",
    "C",
    "程序",
    "输出",
    "打印",
    "printf",
    "计算",
    "结果",
    "和",
    "差",
    "乘",
    "除",
    "比较",
]

UNRELATED_KEYWORDS = ["诗", "联网", "文件", "访问", "下载", "天气"]


def extract_arithmetic_features(input_text: str, ngram_min: int = 1, ngram_max: int = 4) -> Dict[str, float]:
    features: Dict[str, float] = {}
    text = input_text.strip()
    compact = re.sub(r"\s+", "", text)

    for n in range(ngram_min, ngram_max + 1):
        if len(compact) < n:
            continue
        for i in range(len(compact) - n + 1):
            _inc(features, f"char{n}:{compact[i:i+n]}")

    for keyword in KEYWORDS:
        if keyword in text:
            features[f"kw:{keyword}"] = 1.0
    for keyword in UNRELATED_KEYWORDS:
        if keyword in text:
            features[f"unsupported_kw:{keyword}"] = 1.0

    expr = extract_expression_text(text)
    features["has_expression_candidate"] = 1.0 if expr else 0.0
    for op in ["+", "-", "*", "/"]:
        if op in expr:
            features[f"op:{op}"] = 1.0
    features["op_count"] = float(sum(1 for ch in expr if ch in "+-*/"))
    features["has_parentheses"] = 1.0 if "(" in expr or "（" in text else 0.0
    features[f"op_order:{_operator_order(expr)}"] = 1.0

    features["arabic_number_count"] = float(len(re.findall(r"-?\d+", expr)))
    features["chinese_number_count"] = float(sum(1 for ch in expr if ch in CHINESE_DIGITS))
    features["negative_number_count"] = float(len(re.findall(r"(^|[+*/(])-\d+", expr)) + expr.count("负"))
    features["zero_present"] = 1.0 if re.search(r"(^|[^0-9])0([^0-9]|$)", expr) or "零" in expr else 0.0
    features["contains_chinese_punctuation"] = 1.0 if any(ch in text for ch in "，、：（）") else 0.0
    features["contains_english_words"] = 1.0 if re.search(r"[A-Za-z]{3,}\s+[A-Za-z]{3,}", text) else 0.0
    features["input_len_bucket"] = float(min(len(text) // 8, 8))

    try:
        tokens = tokenize_expression(expr) if expr else []
        features["token_count"] = float(len(tokens))
    except ValueError:
        features["invalid_expression_feature"] = 1.0

    parsed = parse_controlled_expression(text)
    if isinstance(parsed, UnsupportedReason):
        if parsed.reason == "division_by_zero":
            features["division_by_zero_signal"] = 1.0
        if parsed.reason == "division_not_exact":
            features["non_exact_division_signal"] = 1.0
    elif parsed:
        features["exact_division_possible"] = 1.0 if "/" in expr else 0.0

    return features


def feature_summary(features: Dict[str, float], limit: int = 20) -> List[str]:
    active = [name for name, value in features.items() if value]
    return sorted(active)[:limit]


def _operator_order(expr: str) -> str:
    order = "".join(ch for ch in expr if ch in "+-*/")
    return order or "none"


def _inc(features: Dict[str, float], name: str, value: float = 1.0):
    features[name] = features.get(name, 0.0) + value
