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
TECHNICAL_TOKENS = ["C", "int", "printf", "main"]


def extract_surface_features(input_text: str) -> Dict:
    text = input_text.strip()
    normalized = text.replace("（", "(").replace("）", ")").replace("，", ",").replace("、", ",")
    signed_numbers = _extract_signed_numbers(normalized)
    chinese_numbers = _extract_chinese_numbers(normalized)
    operators = _operator_sequence(normalized)
    chinese_char_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    english_char_count = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))
    visible_count = max(sum(1 for ch in text if not ch.isspace()), 1)
    is_pure_math = _is_pure_math_expression(normalized)
    has_c_token = bool(re.search(r"(?<![A-Za-z])C(?![A-Za-z])", text))
    has_printf_token = "printf" in text
    has_main_token = bool(re.search(r"\bmain\b", text))
    has_technical = has_c_token or has_printf_token or has_main_token or bool(re.search(r"\bint\b", text))
    contains_output = any(keyword in text for keyword in ["输出", "打印", "计算", "结果"])
    contains_program = "程序" in text or has_main_token
    return {
        "contains_C": has_c_token,
        "contains_program": contains_program,
        "contains_output": contains_output,
        "contains_printf": has_printf_token,
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
        "input_mode_guess_zh_natural": bool(chinese_char_count and contains_output and not has_technical),
        "input_mode_guess_math_expression": is_pure_math,
        "input_mode_guess_zh_technical_mixed": bool(chinese_char_count and has_technical),
        "contains_chinese_chars": bool(chinese_char_count),
        "chinese_char_ratio": round(chinese_char_count / visible_count, 4),
        "english_char_ratio": round(english_char_count / visible_count, 4),
        "is_pure_math_expression": is_pure_math,
        "has_c_token": has_c_token,
        "has_printf_token": has_printf_token,
        "has_main_token": has_main_token,
        "has_technical_token": has_technical,
    }


def numeric_feature_view(features: Dict) -> Dict[str, int]:
    names = [
        "contains_C",
        "contains_program",
        "contains_output",
        "contains_printf",
        "contains_arithmetic_operator",
        "contains_plus",
        "contains_minus",
        "contains_mul",
        "contains_div",
        "contains_parentheses",
        "has_english_sentence",
        "unrelated_keyword_signal",
        "dangerous_keyword_signal",
        "has_chinese_number",
        "has_negative",
        "input_mode_guess_zh_natural",
        "input_mode_guess_math_expression",
        "input_mode_guess_zh_technical_mixed",
        "contains_chinese_chars",
        "is_pure_math_expression",
        "has_c_token",
        "has_printf_token",
        "has_main_token",
        "has_technical_token",
    ]
    numeric = {name: int(features.get(name, False)) for name in names}
    numeric["number_count"] = int(features.get("number_count", 0))
    numeric["operator_count"] = int(features.get("operator_count", 0))
    numeric["chinese_char_ratio_bucket"] = int(float(features.get("chinese_char_ratio", 0.0)) * 10)
    numeric["english_char_ratio_bucket"] = int(float(features.get("english_char_ratio", 0.0)) * 10)
    return numeric


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


def _operator_sequence(text: str) -> str:
    ops = [ch for ch in text if ch in "+-*/"]
    if ops:
        return "".join(ops)
    word_ops = []
    for ch in text:
        if ch == "加":
            word_ops.append("+")
        elif ch == "减":
            word_ops.append("-")
        elif ch == "乘":
            word_ops.append("*")
        elif ch in {"除"}:
            word_ops.append("/")
    return "".join(word_ops)


def _is_pure_math_expression(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return False
    return bool(re.fullmatch(r"[-+*/()0-9一二两三四五六七八九十负]+", compact)) and any(ch in compact for ch in "+-*/加减乘除")
