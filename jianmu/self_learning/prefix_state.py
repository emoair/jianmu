import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.ir_tokens import IRToken


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


@dataclass
class PrefixState:
    input_text: str
    prefix_tokens: List[IRToken]
    step_index: int
    input_features: Optional[Dict] = None
    prefix_features: Optional[Dict] = None

    def __post_init__(self):
        if self.input_features is None:
            self.input_features = extract_input_features(self.input_text)
        if self.prefix_features is None:
            self.prefix_features = extract_prefix_features(self.prefix_tokens)


def extract_input_features(input_text: str) -> Dict:
    numbers = _extract_numbers(input_text)
    return {
        "has_c_program": bool(re.search(r"\bC\b|程序", input_text, re.IGNORECASE)),
        "has_output": any(token in input_text for token in ["输出", "打印", "printf"]),
        "numbers": numbers,
        "is_addition_task": "+" in input_text and len(numbers) >= 2,
    }


def extract_prefix_features(prefix_tokens: List[IRToken]) -> Dict:
    token_types = [token.type for token in prefix_tokens]
    return {
        "prefix_length": len(prefix_tokens),
        "last_token_type": token_types[-1] if token_types else None,
        "has_include": "INCLUDE_STDIO" in token_types,
        "has_main_begin": "MAIN_BEGIN" in token_types,
        "literal_count": sum(1 for token_type in token_types if token_type == "LITERAL_INT"),
        "has_add": "ADD" in token_types,
        "has_print": "PRINT_EXPR" in token_types,
        "is_complete": bool(token_types and token_types[-1] == "MAIN_END"),
    }


def _extract_numbers(input_text: str) -> List[int]:
    found = []
    for match in re.finditer(r"-?\d+|[零一二两三四五六七八九十]", input_text):
        token = match.group(0)
        if token in CHINESE_DIGITS:
            next_char = input_text[match.end():match.end() + 1]
            if next_char in {"个", "個"}:
                continue
            found.append(CHINESE_DIGITS[token])
        else:
            found.append(int(token))
    return found
