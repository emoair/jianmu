from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


class ArithmeticEvaluationError(ValueError):
    pass


@dataclass(frozen=True)
class EvalConfig:
    max_depth: int = 5
    max_operator_count: int = 8
    max_result_abs: int = 1_000_000


class ArithmeticParser:
    def __init__(self, text: str) -> None:
        self.text = text.replace(" ", "")
        self.pos = 0

    def parse(self) -> Dict[str, Any]:
        if not self.text:
            raise ArithmeticEvaluationError("empty expression")
        node = self._expr()
        if self.pos != len(self.text):
            raise ArithmeticEvaluationError("trailing input")
        return node

    def _expr(self) -> Dict[str, Any]:
        node = self._term()
        while self._peek() in {"+", "-"}:
            op = self._take()
            right = self._term()
            node = {"op": "add" if op == "+" else "sub", "args": [node, right]}
        return node

    def _term(self) -> Dict[str, Any]:
        node = self._factor()
        while self._peek() in {"*", "/"}:
            op = self._take()
            right = self._factor()
            node = {"op": "mul" if op == "*" else "div_exact", "args": [node, right]}
        return node

    def _factor(self) -> Dict[str, Any]:
        ch = self._peek()
        if ch == "-":
            self._take()
            return {"op": "neg", "arg": self._factor()}
        if ch == "(":
            self._take()
            node = self._expr()
            if self._peek() != ")":
                raise ArithmeticEvaluationError("missing closing parenthesis")
            self._take()
            return node
        return self._int()

    def _int(self) -> Dict[str, Any]:
        start = self.pos
        while self._peek() is not None and self._peek().isdigit():
            self._take()
        if start == self.pos:
            raise ArithmeticEvaluationError("expected integer")
        return {"op": "int", "value": int(self.text[start:self.pos])}

    def _peek(self) -> str | None:
        return self.text[self.pos] if self.pos < len(self.text) else None

    def _take(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch


def parse_expression(text: str) -> Dict[str, Any]:
    return ArithmeticParser(text).parse()


def evaluate_target_ir(node: Dict[str, Any], config: EvalConfig | None = None) -> int:
    config = config or EvalConfig()
    value, depth, ops = _eval(node)
    if depth > config.max_depth:
        raise ArithmeticEvaluationError("depth limit exceeded")
    if ops > config.max_operator_count:
        raise ArithmeticEvaluationError("operator limit exceeded")
    if abs(value) > config.max_result_abs:
        raise ArithmeticEvaluationError("result limit exceeded")
    return value


def safe_evaluate_expression(text: str, config: EvalConfig | None = None) -> Tuple[int, Dict[str, Any]]:
    node = parse_expression(text)
    return evaluate_target_ir(node, config), node


def _eval(node: Dict[str, Any]) -> Tuple[int, int, int]:
    op = node.get("op")
    if op == "int":
        return int(node["value"]), 1, 0
    if op == "neg":
        value, depth, ops = _eval(node["arg"])
        return -value, depth + 1, ops + 1
    if op in {"add", "sub", "mul", "div_exact"}:
        left, right = node["args"]
        lv, ld, lo = _eval(left)
        rv, rd, ro = _eval(right)
        if op == "add":
            value = lv + rv
        elif op == "sub":
            value = lv - rv
        elif op == "mul":
            value = lv * rv
        else:
            if rv == 0:
                raise ArithmeticEvaluationError("division by zero")
            if lv % rv != 0:
                raise ArithmeticEvaluationError("non-integer division")
            value = lv // rv
        return value, max(ld, rd) + 1, lo + ro + 1
    raise ArithmeticEvaluationError(f"unknown op: {op}")


def target_ir_to_expression(node: Dict[str, Any]) -> str:
    op = node.get("op")
    if op == "int":
        return str(node["value"])
    if op == "neg":
        return f"(-{target_ir_to_expression(node['arg'])})"
    if op in {"add", "sub", "mul", "div_exact"}:
        symbol = {"add": "+", "sub": "-", "mul": "*", "div_exact": "/"}[op]
        left, right = node["args"]
        return f"({target_ir_to_expression(left)} {symbol} {target_ir_to_expression(right)})"
    raise ArithmeticEvaluationError(f"unknown op: {op}")


def inspect_ir(node: Dict[str, Any]) -> Dict[str, Any]:
    ops: List[str] = []

    def walk(n: Dict[str, Any], depth: int = 1) -> int:
        op = n["op"]
        if op == "int":
            return depth
        ops.append(op)
        if op == "neg":
            return walk(n["arg"], depth + 1)
        return max(walk(child, depth + 1) for child in n["args"])

    depth = walk(node)
    return {
        "operator_set": sorted(set(ops)),
        "operator_count": len(ops),
        "expression_depth": depth,
        "has_unary_minus": "neg" in ops,
        "has_division": "div_exact" in ops,
    }
