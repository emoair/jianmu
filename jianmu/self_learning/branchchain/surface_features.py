import re
from typing import Dict, List


CHINESE_NUMBERS = {
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

UNRELATED_KEYWORDS = ["诗", "天气", "故事", "笑话", "新闻"]
DANGEROUS_KEYWORDS = ["联网", "下载", "访问文件", "删除文件", "API key", "token"]


def extract_surface_features(input_text: str) -> Dict:
    text = input_text.strip()
    normalized = text.replace("（", "(").replace("）", ")")
    signed_numbers = _extract_signed_numbers(normalized)
    chinese_numbers = _extract_chinese_numbers(normalized)
    operators = "".join(ch for ch in normalized if ch in "+-*/")
    return {
        "contains_C": "C" in text,
        "contains_program": "程序" in text or "main" in text,
        "contains_output": "输出" in text or "打印" in text,
        "contains_printf": "printf" in text,
        "contains_arithmetic_operator": bool(operators),
        "contains_plus": "+" in operators,
        "contains_minus": "-" in operators,
        "contains_mul": "*" in operators,
        "contains_div": "/" in operators,
        "contains_parentheses": "(" in normalized and ")" in normalized,
        "arabic_numbers": signed_numbers,
        "chinese_numbers": chinese_numbers,
        "signed_numbers": signed_numbers + chinese_numbers,
        "operator_sequence": operators,
        "number_count": len(signed_numbers) + len(chinese_numbers),
        "operator_count": len(operators),
        "has_english_sentence": bool(re.search(r"[A-Za-z]{3,}\s+[A-Za-z]{3,}", text)),
        "unrelated_keyword_signal": any(keyword in text for keyword in UNRELATED_KEYWORDS),
        "dangerous_keyword_signal": any(keyword in text for keyword in DANGEROUS_KEYWORDS),
        "has_chinese_number": bool(chinese_numbers),
        "has_negative": any(value < 0 for value in signed_numbers + chinese_numbers),
    }


def numeric_feature_view(features: Dict) -> Dict[str, int]:
    return {
        "contains_C": int(features.get("contains_C", False)),
        "contains_program": int(features.get("contains_program", False)),
        "contains_output": int(features.get("contains_output", False)),
        "contains_printf": int(features.get("contains_printf", False)),
        "contains_arithmetic_operator": int(features.get("contains_arithmetic_operator", False)),
        "contains_plus": int(features.get("contains_plus", False)),
        "contains_minus": int(features.get("contains_minus", False)),
        "contains_mul": int(features.get("contains_mul", False)),
        "contains_div": int(features.get("contains_div", False)),
        "contains_parentheses": int(features.get("contains_parentheses", False)),
        "number_count": int(features.get("number_count", 0)),
        "operator_count": int(features.get("operator_count", 0)),
        "has_english_sentence": int(features.get("has_english_sentence", False)),
        "unrelated_keyword_signal": int(features.get("unrelated_keyword_signal", False)),
        "dangerous_keyword_signal": int(features.get("dangerous_keyword_signal", False)),
        "has_chinese_number": int(features.get("has_chinese_number", False)),
        "has_negative": int(features.get("has_negative", False)),
    }


def _extract_signed_numbers(text: str) -> List[int]:
    values = []
    for match in re.finditer(r"(?<![A-Za-z0-9])-?\d+", text):
        values.append(int(match.group(0)))
    return values


def _extract_chinese_numbers(text: str) -> List[int]:
    values = []
    for index, ch in enumerate(text):
        if ch not in CHINESE_NUMBERS:
            continue
        if ch == "一" and index + 1 < len(text) and text[index + 1] in {"个", "首", "段"}:
            continue
        value = CHINESE_NUMBERS[ch]
        if index > 0 and text[index - 1] == "负":
            value = -value
        values.append(value)
    return values
