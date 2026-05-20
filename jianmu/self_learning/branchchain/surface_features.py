import re
from typing import Dict, List


ZH_NUMERAL_CHARS = set("零一二两三四五六七八九十")
ZH_OPERATOR_WORDS = ["除以", "加上", "减去", "乘以", "加", "减", "乘", "除"]

UNRELATED_KEYWORDS = ["诗", "天气", "故事", "笑话", "新闻"]
DANGEROUS_KEYWORDS = ["联网", "下载", "访问文件", "删除文件", "API key", "token"]
TECHNICAL_TOKENS = ["C", "int", "printf", "main"]


def extract_surface_features(input_text: str) -> Dict:
    text = input_text.strip()
    normalized = text.replace("（", "(").replace("）", ")").replace("，", ",").replace("、", ",")
    signed_numbers = _extract_signed_numbers(normalized)
    operators = _operator_sequence(normalized)
    raw_numeral_chars = [ch for ch in text if ch in ZH_NUMERAL_CHARS]
    raw_operator_words = _raw_operator_words(text)
    char_ngrams = _raw_char_ngrams(text)
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
    unary_negative_only = len(signed_numbers) == 1 and signed_numbers[0] < 0 and not operators
    signed_literal_only = len(signed_numbers) == 1 and not operators
    binary_minus_present = "-" in operators
    division_by_zero_signal = _division_by_zero_signal(signed_numbers, operators)
    non_exact_division_signal = _non_exact_division_signal(signed_numbers, operators)
    unsupported_depth_signal = len(signed_numbers) > 3 or len(operators) > 2
    unsupported_arithmetic_signal = division_by_zero_signal or non_exact_division_signal or unsupported_depth_signal
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
        "chinese_numbers": [],
        "signed_numbers": signed_numbers,
        "operator_sequence": operators,
        "number_count": len(signed_numbers),
        "operator_count": len(operators),
        "has_english_sentence": bool(re.search(r"[A-Za-z]{3,}\s+[A-Za-z]{3,}", text)),
        "unrelated_keyword_signal": any(keyword in text for keyword in UNRELATED_KEYWORDS),
        "dangerous_keyword_signal": any(keyword in text for keyword in DANGEROUS_KEYWORDS),
        "has_chinese_number": bool(raw_numeral_chars),
        "has_negative": any(value < 0 for value in signed_numbers) or "负" in text,
        "unary_negative_only": unary_negative_only,
        "signed_literal_only": signed_literal_only,
        "binary_minus_present": binary_minus_present,
        "unsupported_arithmetic_signal": unsupported_arithmetic_signal,
        "division_by_zero_signal": division_by_zero_signal,
        "non_exact_division_signal": non_exact_division_signal,
        "unsupported_depth_signal": unsupported_depth_signal,
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
        "contains_zh_numeral_char": bool(raw_numeral_chars),
        "zh_numeral_char_count": len(raw_numeral_chars),
        "zh_numeral_chars_present": "".join(sorted(set(raw_numeral_chars))),
        "contains_zh_operator_word": bool(raw_operator_words),
        "zh_operator_words_present": "|".join(raw_operator_words),
        "contains_negative_zh_marker": "负" in text,
        "contains_parenthesis_zh_marker": "括号" in text or "（" in text or "）" in text,
        "contains_equal_question_pattern": any(token in text for token in ["等于多少", "结果", "多少", "值"]),
        "raw_char_ngrams_1": char_ngrams[1],
        "raw_char_ngrams_2": char_ngrams[2],
        "raw_char_ngrams_3": char_ngrams[3],
        "digit_char_ratio": round(sum(1 for ch in text if ch.isdigit()) / visible_count, 4),
        "ascii_operator_ratio": round(sum(1 for ch in text if ch in "+-*/") / visible_count, 4),
    }


def extract_canonical_surface_features(input_text: str, canonicalization_enabled: bool = True) -> Dict:
    """Extract features after Canonical Symbol Layer（规范符号层） preprocessing."""
    if not canonicalization_enabled:
        features = extract_surface_features(input_text)
        features.update(
            {
                "raw_text": input_text,
                "canonical_text": input_text,
                "canonical_changed": False,
                "canonical_token_count": 0,
                "source_map_coverage": 0.0,
                "contains_canonicalized_zh_number": False,
                "contains_canonicalized_zh_operator": False,
            }
        )
        return features
    from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols

    canonical = canonicalize_symbols(input_text)
    routed_text = canonical.canonical_text or input_text
    features = extract_surface_features(routed_text)
    non_text = [token for token in canonical.tokens if token.token_type != "TEXT"]
    mapped = [token for token in non_text if token.raw and token.canonical]
    features.update(
        {
            "raw_text": input_text,
            "canonical_text": routed_text,
            "canonical_changed": canonical.changed,
            "canonical_token_count": len(canonical.tokens),
            "source_map_coverage": round(len(mapped) / max(len(non_text), 1), 4),
            "contains_canonicalized_zh_number": any(
                token.token_type == "NUM" and token.raw != token.canonical for token in canonical.tokens
            ),
            "contains_canonicalized_zh_operator": any(
                token.token_type.startswith("OP_") and token.raw != token.canonical for token in canonical.tokens
            ),
        }
    )
    return features


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
        "contains_zh_numeral_char",
        "contains_zh_operator_word",
        "contains_negative_zh_marker",
        "contains_parenthesis_zh_marker",
        "contains_equal_question_pattern",
        "canonical_changed",
        "contains_canonicalized_zh_number",
        "contains_canonicalized_zh_operator",
        "unary_negative_only",
        "signed_literal_only",
        "binary_minus_present",
        "unsupported_arithmetic_signal",
        "division_by_zero_signal",
        "non_exact_division_signal",
        "unsupported_depth_signal",
    ]
    numeric = {name: int(features.get(name, False)) for name in names}
    numeric["number_count"] = int(features.get("number_count", 0))
    numeric["operator_count"] = int(features.get("operator_count", 0))
    numeric["zh_numeral_char_count"] = int(features.get("zh_numeral_char_count", 0))
    numeric["chinese_char_ratio_bucket"] = int(float(features.get("chinese_char_ratio", 0.0)) * 10)
    numeric["english_char_ratio_bucket"] = int(float(features.get("english_char_ratio", 0.0)) * 10)
    numeric["digit_char_ratio_bucket"] = int(float(features.get("digit_char_ratio", 0.0)) * 10)
    numeric["ascii_operator_ratio_bucket"] = int(float(features.get("ascii_operator_ratio", 0.0)) * 10)
    return numeric


def _extract_signed_numbers(text: str) -> List[int]:
    values = []
    for match in re.finditer(r"(?<![A-Za-z0-9])-?\d+", text):
        values.append(int(match.group(0)))
    return values


def _operator_sequence(text: str) -> str:
    operators = []
    compact = re.sub(r"\s+", "", text)
    for index, ch in enumerate(compact):
        if ch not in "+-*/":
            continue
        if ch == "-" and index + 1 < len(compact) and compact[index + 1].isdigit():
            previous = compact[index - 1] if index > 0 else ""
            if index == 0 or previous in "(+-*/":
                continue
        operators.append(ch)
    return "".join(operators)


def _is_pure_math_expression(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return False
    return bool(re.fullmatch(r"[-+*/()0-9一二两三四五六七八九十负]+", compact)) and any(ch in compact for ch in "+-*/加减乘除")


def _division_by_zero_signal(numbers: List[int], operators: str) -> bool:
    for index, operator in enumerate(operators):
        if operator == "/" and index + 1 < len(numbers) and numbers[index + 1] == 0:
            return True
    return False


def _non_exact_division_signal(numbers: List[int], operators: str) -> bool:
    for index, operator in enumerate(operators):
        if operator != "/" or index + 1 >= len(numbers):
            continue
        denominator = numbers[index + 1]
        if denominator != 0 and numbers[index] % denominator != 0:
            return True
    return False


def _raw_operator_words(text: str) -> List[str]:
    return [word for word in ZH_OPERATOR_WORDS if word in text]


def _raw_char_ngrams(text: str) -> Dict[int, str]:
    compact = re.sub(r"\s+", "", text)
    return {
        n: "|".join(compact[index:index + n] for index in range(max(len(compact) - n + 1, 0)))
        for n in (1, 2, 3)
    }
