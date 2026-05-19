import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from jianmu.self_learning.arithmetic_targetir.target_ir import ArithmeticNode, ArithmeticTargetIR


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


@dataclass(frozen=True)
class UnsupportedReason:
    reason: str
    detail: str = ""


Token = Tuple[str, Union[int, str]]


def parse_controlled_expression(expr_text: str) -> Union[ArithmeticTargetIR, UnsupportedReason]:
    candidate = extract_expression_text(expr_text)
    if not candidate:
        return UnsupportedReason("invalid_expression", "no controlled arithmetic expression found")
    try:
        tokens = tokenize_expression(candidate)
        parser = _Parser(tokens)
        root = parser.parse()
        if parser.has_remaining():
            return UnsupportedReason("invalid_expression", "trailing tokens")
        ir = ArithmeticTargetIR(root=root)
        ir.root.evaluate()
        return ir
    except ZeroDivisionError:
        return UnsupportedReason("division_by_zero")
    except ValueError as exc:
        if "not exact" in str(exc):
            return UnsupportedReason("division_not_exact")
        return UnsupportedReason("invalid_expression", str(exc))


def extract_expression_text(input_text: str) -> str:
    normalized = input_text.replace("（", "(").replace("）", ")")
    allowed = set("0123456789+-*/() 　负零一二两三四五六七八九十")
    chunks: List[str] = []
    current: List[str] = []
    for ch in normalized:
        if ch in allowed:
            current.append(ch)
        else:
            if current:
                chunks.append("".join(current))
                current = []
    if current:
        chunks.append("".join(current))

    candidates = []
    for chunk in chunks:
        compact = re.sub(r"\s+", "", chunk)
        if not compact:
            continue
        has_binary_operator = any(op in compact for op in ["+", "*", "/"]) or _has_binary_minus(compact)
        has_number = bool(re.search(r"\d", compact)) or any(ch in CHINESE_DIGITS for ch in compact)
        if has_binary_operator and has_number:
            candidates.append(compact)
    return max(candidates, key=len) if candidates else ""


def tokenize_expression(expr_text: str) -> List[Token]:
    text = expr_text.replace("（", "(").replace("）", ")")
    tokens: List[Token] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit():
            j = i + 1
            while j < len(text) and text[j].isdigit():
                j += 1
            tokens.append(("INT", int(text[i:j])))
            i = j
            continue
        if ch in CHINESE_DIGITS:
            tokens.append(("INT", CHINESE_DIGITS[ch]))
            i += 1
            continue
        if ch == "负":
            tokens.append(("NEG", ch))
            i += 1
            continue
        if ch in "+-*/()":
            token_type = "LPAREN" if ch == "(" else "RPAREN" if ch == ")" else "OP"
            tokens.append((token_type, ch))
            i += 1
            continue
        raise ValueError(f"unsupported expression character: {ch}")
    return tokens


def parse_canonical(canonical: str) -> ArithmeticNode:
    tokens = re.findall(r"add|sub|mul|div|lit|-?\d+|[(),]", canonical)
    index = 0

    def parse_node() -> ArithmeticNode:
        nonlocal index
        if index >= len(tokens):
            raise ValueError("unexpected end of canonical expression")
        head = tokens[index]
        index += 1
        if head == "lit":
            _expect("(")
            value = int(tokens[index])
            index += 1
            _expect(")")
            return ArithmeticNode.literal(value)
        if head not in {"add", "sub", "mul", "div"}:
            raise ValueError(f"unsupported canonical head: {head}")
        _expect("(")
        left = parse_node()
        _expect(",")
        right = parse_node()
        _expect(")")
        return ArithmeticNode.op(head, left, right)

    def _expect(expected: str):
        nonlocal index
        if index >= len(tokens) or tokens[index] != expected:
            raise ValueError(f"expected {expected}")
        index += 1

    node = parse_node()
    if index != len(tokens):
        raise ValueError("trailing canonical tokens")
    return node


def _has_binary_minus(text: str) -> bool:
    for i, ch in enumerate(text):
        if ch != "-":
            continue
        if i == 0:
            continue
        prev = text[i - 1]
        if prev in "+-*/(":
            continue
        return True
    return False


class _Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def parse(self) -> ArithmeticNode:
        if not self.tokens:
            raise ValueError("empty expression")
        return self._parse_add_sub()

    def has_remaining(self) -> bool:
        return self.index != len(self.tokens)

    def _peek(self) -> Optional[Token]:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _advance(self) -> Token:
        token = self.tokens[self.index]
        self.index += 1
        return token

    def _parse_add_sub(self) -> ArithmeticNode:
        node = self._parse_mul_div()
        while self._peek() == ("OP", "+") or self._peek() == ("OP", "-"):
            op = self._advance()[1]
            right = self._parse_mul_div()
            node = ArithmeticNode.op("add" if op == "+" else "sub", node, right)
        return node

    def _parse_mul_div(self) -> ArithmeticNode:
        node = self._parse_factor()
        while self._peek() == ("OP", "*") or self._peek() == ("OP", "/"):
            op = self._advance()[1]
            right = self._parse_factor()
            candidate = ArithmeticNode.op("mul" if op == "*" else "div", node, right)
            if op == "/":
                candidate.evaluate()
            node = candidate
        return node

    def _parse_factor(self) -> ArithmeticNode:
        token = self._peek()
        if token is None:
            raise ValueError("expected factor")
        if token[0] == "NEG" or token == ("OP", "-"):
            self._advance()
            factor = self._parse_factor()
            if factor.kind == "literal":
                return ArithmeticNode.literal(-factor.value)
            return ArithmeticNode.op("sub", ArithmeticNode.literal(0), factor)
        if token[0] == "INT":
            self._advance()
            return ArithmeticNode.literal(int(token[1]))
        if token[0] == "LPAREN":
            self._advance()
            node = self._parse_add_sub()
            if self._peek() is None or self._peek()[0] != "RPAREN":
                raise ValueError("missing closing parenthesis")
            self._advance()
            return node
        raise ValueError(f"expected factor, got {token}")

