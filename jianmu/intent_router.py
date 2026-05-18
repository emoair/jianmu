import re

from jianmu.semantic_neurons import is_unsupported_english_natural_language


CHINESE_NUM = {
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


def _cn_to_int(token: str):
    if token in CHINESE_NUM:
        return CHINESE_NUM[token]
    if token.isdigit():
        return int(token)
    return None


def _parse_num(text: str):
    """Extract the first Chinese numeral or digit count."""
    count_token = r"([一二两三四五六七八九十\d]+)"
    for pattern in [
        count_token + r"\s*(?:个)?\s*(?:整数|int|加数|变量|数)",
        r"算\s*" + count_token,
        count_token + r"\s*(?:个)?\s*1\s*的和",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            value = _cn_to_int(m.group(1))
            if value:
                return value

    found = None
    for ch in text:
        if ch in CHINESE_NUM:
            found = CHINESE_NUM[ch]
    if found:
        return found
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def _parse_target_num(text: str):
    """For expand intents: extract the target operand count."""
    m = re.search(r"(?:改成|变成|扩展成|扩展为|算|输出)([一二两三四五六七八九十\d]+)", text)
    if m:
        v = _cn_to_int(m.group(1))
        if v:
            return v
    return _parse_num(text)


def _parse_values(text: str):
    """
    Extract explicit integer values from Chinese-first input.
    Supports expressions like 1+2+3 and lists like 1、2、3 / 1,2,3.
    """
    expr = re.search(r"-?\d+(?:\s*\+\s*-?\d+)+", text)
    if expr:
        return [int(x) for x in re.findall(r"-?\d+", expr.group())]

    nums = re.findall(r"-?\d+", text)
    if len(nums) < 2:
        return None

    if re.search(r"\d+(?:\s*[、,，]\s*-?\d+)+", text):
        return [int(x) for x in nums]

    if re.search(r"(?:整数|int)\s*[\d\s,，、-]+", text, re.IGNORECASE):
        return [int(x) for x in nums]

    if re.search(r"\d+(?:\s*加\s*-?\d+)+", text):
        return [int(x) for x in nums]

    return None


def _parse_expand_value(text: str):
    """For Chinese append intents, extract the new variable value."""
    m = re.search(r"(?:多加|再加)一?个\s*(?:值?为?\s*)?(-?\d+)", text)
    if m:
        return int(m.group(1))
    for ch, value in CHINESE_NUM.items():
        if re.search(r"(?:多加|再加)一?个" + re.escape(ch), text):
            return value
    return 1


class IntentRouter:
    _EXPAND_PATTERNS = [
        r"改成",
        r"变成",
        r"再加",
        r"多加",
        r"扩展",
        r"输出.{0,6}变量.{0,4}总和",
        r"算.{0,6}的和",
        r"加数",
    ]

    def parse(self, text: str, previous_var_count: int = None) -> dict:
        if is_unsupported_english_natural_language(text):
            return {
                "action": "unsupported_input",
                "reason": "english_natural_language_out_of_scope",
                "operation": "unknown",
                "print": False,
                "language": "unsupported",
            }

        if self._is_expand(text):
            target = _parse_target_num(text)
            if target is None or (
                re.search(r"(?:多加|再加)一个", text) and
                not re.search(r"(?:改成|变成|扩展成|扩展为)", text)
            ):
                target = (previous_var_count + 1) if previous_var_count else None
            new_val = _parse_expand_value(text)
            return {
                "action": "expand_sum_program",
                "target_var_count": target,
                "new_value": new_val,
                "default_value": 1,
                "operation": "sum",
                "print": True,
                "language": "c",
            }

        values = _parse_values(text)
        if values:
            n = len(values)
        else:
            n = _parse_num(text) or 2
            values = [1] * n
        return {
            "action": "generate_sum_program",
            "var_count": n,
            "values": values,
            "operation": "sum",
            "print": True,
            "language": "c",
        }

    def _is_expand(self, text: str) -> bool:
        return any(re.search(p, text) for p in self._EXPAND_PATTERNS)
