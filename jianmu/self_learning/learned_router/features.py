import re
from typing import Dict, Iterable, Tuple


KEYWORDS = {
    "kw_write_one": "写一个",
    "kw_c": "C",
    "kw_program": "程序",
    "kw_output": "输出",
    "kw_printf": "printf",
    "kw_append_again": "再加",
    "kw_add_more": "多加",
    "kw_append": "追加",
    "kw_change_to": "改成",
    "kw_replace": "替换",
    "kw_last": "最后",
    "kw_second": "第二",
    "kw_no": "不要",
    "kw_bie": "别",
    "kw_keep": "保持",
    "kw_from": "从",
    "kw_become": "变成",
}

CHINESE_NUM_RE = re.compile(r"[零一二两三四五六七八九十]")
ARABIC_NUM_RE = re.compile(r"-?\d+")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{2,}")
MINUS_EXPR_RE = re.compile(r"\d+\s*-\s*-?\d+")


def extract_features(input_text: str, ngram_range: Tuple[int, int] = (1, 3)) -> Dict[str, float]:
    features: Dict[str, float] = {}
    text = input_text.strip()

    for n in range(ngram_range[0], ngram_range[1] + 1):
        for gram in _char_ngrams(text, n):
            features[f"char{n}:{gram}"] = features.get(f"char{n}:{gram}", 0.0) + 1.0

    for name, token in KEYWORDS.items():
        if token in text:
            features[name] = 1.0

    arabic_numbers = ARABIC_NUM_RE.findall(text)
    chinese_numbers = CHINESE_NUM_RE.findall(text)
    negative_numbers = [num for num in arabic_numbers if num.startswith("-")]
    if "负" in text:
        negative_numbers.append("负")

    features["num_arabic_count"] = float(len(arabic_numbers))
    features["num_chinese_count"] = float(len(chinese_numbers))
    features["num_negative_count"] = float(len(negative_numbers))
    features["has_plus"] = 1.0 if "+" in text else 0.0
    features["has_minus_expression"] = 1.0 if MINUS_EXPR_RE.search(text) else 0.0
    features["has_multiply"] = 1.0 if "*" in text else 0.0
    features["has_divide"] = 1.0 if "/" in text else 0.0

    features["tech_c"] = 1.0 if re.search(r"\bC\b", text) else 0.0
    features["tech_int"] = 1.0 if re.search(r"\bint\b", text) else 0.0
    features["tech_printf"] = 1.0 if "printf" in text else 0.0
    features["tech_main"] = 1.0 if re.search(r"\bmain\b", text) else 0.0

    features[f"length_bucket:{_length_bucket(len(text))}"] = 1.0
    features["punct_chinese"] = 1.0 if any(ch in text for ch in "，、：（）") else 0.0
    features["punct_spaces"] = 1.0 if " " in text else 0.0
    features["contains_english_words"] = 1.0 if ENGLISH_WORD_RE.search(text) else 0.0
    features["english_natural_language_signal"] = 1.0 if _english_nl_signal(text) else 0.0
    return features


def summarize_features(features: Dict[str, float]) -> Dict[str, float]:
    summary_keys = [
        "num_arabic_count",
        "num_chinese_count",
        "num_negative_count",
        "has_plus",
        "has_minus_expression",
        "has_multiply",
        "has_divide",
        "tech_c",
        "tech_int",
        "tech_printf",
        "tech_main",
        "contains_english_words",
        "english_natural_language_signal",
    ]
    return {key: features.get(key, 0.0) for key in summary_keys}


def _char_ngrams(text: str, n: int) -> Iterable[str]:
    if n <= 0 or len(text) < n:
        return []
    return (text[i:i + n] for i in range(len(text) - n + 1))


def _length_bucket(length: int) -> str:
    if length <= 8:
        return "short"
    if length <= 20:
        return "medium"
    return "long"


def _english_nl_signal(text: str) -> bool:
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return False
    return bool(re.search(r"\b(sum|add|calculate|print|numbers?)\b", text.lower()))

