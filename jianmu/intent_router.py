import re

CHINESE_NUM = {"两": 2, "三": 3, "四": 4, "五": 5, "六": 6}

# English number words
ENGLISH_NUM = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _cn_to_int(token: str):
    if token in CHINESE_NUM:
        return CHINESE_NUM[token]
    if token.isdigit():
        return int(token)
    return None


def _parse_num(text: str):
    """Extract first number (Chinese word or digit) from text."""
    for ch, n in CHINESE_NUM.items():
        if ch in text:
            return n
    for w, n in ENGLISH_NUM.items():
        if re.search(r'\b' + w + r'\b', text, re.IGNORECASE):
            return n
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def _parse_target_num(text: str):
    """For expand intents: extract the *target* count."""
    # Chinese: 改成/变成/扩展成/扩展为/多加一个/再加一个 + number
    m = re.search(r"(?:改成|变成|扩展成|扩展为|算|输出)([两三四五六\d]+)", text)
    if m:
        v = _cn_to_int(m.group(1))
        if v:
            return v
    # English: "sum of N numbers/integers"
    m = re.search(r"sum\s+of\s+(\w+)\s+(?:numbers?|integers?)", text, re.IGNORECASE)
    if m:
        token = m.group(1).lower()
        if token in ENGLISH_NUM:
            return ENGLISH_NUM[token]
        if token.isdigit():
            return int(token)
    return _parse_num(text)


def _parse_values(text: str):
    """
    Extract explicit values list from text.
    Handles:
      - "1加2加3"  → [1,2,3]
      - "定义三个整数 1 2 3" → [1,2,3]
      - "整数 1 2 3" → [1,2,3]
    Returns None if no explicit values found.
    """
    # Pattern: digits separated by 加/空格/逗号
    # "1加2加3" or "1 2 3" or "1,2,3"
    m = re.findall(r"\d+", text)
    if len(m) >= 2:
        # Heuristic: if all numbers appear in an arithmetic-like context
        # Check for "X加Y加Z" pattern
        if re.search(r"\d+(?:加\d+)+", text):
            return [int(x) for x in re.findall(r"\d+", re.search(r"[\d加]+", text).group())]
        # Check for "整数 1 2 3" or "定义...1 2 3"
        if re.search(r"(?:整数|int|integer)\s+[\d\s,]+", text, re.IGNORECASE):
            nums = re.findall(r"\d+", re.search(r"(?:整数|int|integer)\s+([\d\s,]+)", text, re.IGNORECASE).group(1))
            if len(nums) >= 2:
                return [int(x) for x in nums]
    return None


def _parse_expand_value(text: str):
    """For 'add one more with value X' — extract the new variable's value."""
    # "多加一个 2" / "再加一个 2" / "多加一个值为2"
    m = re.search(r"(?:多加|再加)一个\s*(?:值?为?\s*)?(\d+)", text)
    if m:
        return int(m.group(1))
    return 1  # default


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
        if self._is_expand(text):
            target = _parse_target_num(text)
            # "多加一个" / "再加一个" without explicit target → increment by 1
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
        else:
            # Try to extract explicit values first
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
