import json
from dataclasses import dataclass
from typing import Dict, List, Optional


SUPPORTED_NODE_KINDS = {"literal", "add", "sub", "mul", "div"}
OP_SYMBOLS = {"add": "+", "sub": "-", "mul": "*", "div": "/"}
TOKEN_TYPES = {"add": "ADD", "sub": "SUB", "mul": "MUL", "div": "DIV"}


@dataclass(frozen=True)
class ArithmeticNode:
    kind: str
    value: Optional[int] = None
    left: Optional["ArithmeticNode"] = None
    right: Optional["ArithmeticNode"] = None

    def __post_init__(self):
        if self.kind not in SUPPORTED_NODE_KINDS:
            raise ValueError(f"unsupported ArithmeticNode kind: {self.kind}")
        if self.kind == "literal":
            if self.value is None:
                raise ValueError("literal node requires value")
        elif self.left is None or self.right is None:
            raise ValueError(f"{self.kind} node requires left and right")

    @classmethod
    def literal(cls, value: int) -> "ArithmeticNode":
        return cls(kind="literal", value=int(value))

    @classmethod
    def op(cls, kind: str, left: "ArithmeticNode", right: "ArithmeticNode") -> "ArithmeticNode":
        return cls(kind=kind, left=left, right=right)

    def canonical(self) -> str:
        if self.kind == "literal":
            return f"lit({self.value})"
        return f"{self.kind}({self.left.canonical()},{self.right.canonical()})"

    def to_c_expr(self) -> str:
        if self.kind == "literal":
            return str(self.value)
        return f"({self.left.to_c_expr()} {OP_SYMBOLS[self.kind]} {self.right.to_c_expr()})"

    def evaluate(self) -> int:
        if self.kind == "literal":
            return int(self.value)
        left = self.left.evaluate()
        right = self.right.evaluate()
        if self.kind == "add":
            return left + right
        if self.kind == "sub":
            return left - right
        if self.kind == "mul":
            return left * right
        if right == 0:
            raise ZeroDivisionError("division by zero")
        if left % right != 0:
            raise ValueError("division is not exact")
        return int(left / right)

    def postorder_tokens(self) -> List[Dict]:
        if self.kind == "literal":
            return [{"type": "LITERAL_INT", "value": self.value}]
        return self.left.postorder_tokens() + self.right.postorder_tokens() + [{"type": TOKEN_TYPES[self.kind]}]


@dataclass(frozen=True)
class ArithmeticTargetIR:
    root: ArithmeticNode
    source_mode: str = "new_target"
    provenance: str = "oracle_expression"

    @property
    def canonical_expr(self) -> str:
        return self.root.canonical()

    @property
    def c_expr(self) -> str:
        return self.root.to_c_expr()

    @property
    def expected_output(self) -> str:
        return f"{self.root.evaluate()}\n"

    def to_c_program(self) -> str:
        return (
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            f"    printf(\"%d\\n\", {self.c_expr});\n"
            "    return 0;\n"
            "}\n"
        )

    def to_dict(self) -> Dict:
        return {
            "canonical": self.canonical_expr,
            "c_expr": self.c_expr,
            "expected_output": self.expected_output,
            "source_mode": self.source_mode,
            "provenance": self.provenance,
        }

    def program_ir_tokens(self) -> List[Dict]:
        return self.root.postorder_tokens()

    def structural_equals(self, other: "ArithmeticTargetIR") -> bool:
        return bool(other) and self.canonical_expr == other.canonical_expr


def target_ir_from_json(payload: Dict) -> ArithmeticTargetIR:
    from jianmu.self_learning.arithmetic_targetir.expression_oracle import parse_canonical

    return ArithmeticTargetIR(
        root=parse_canonical(payload["canonical"]),
        source_mode=payload.get("source_mode", "regenerated_target"),
        provenance=payload.get("provenance", "oracle_expression"),
    )


def target_ir_to_json_line(ir: ArithmeticTargetIR) -> str:
    return json.dumps(ir.to_dict(), ensure_ascii=False, sort_keys=True)

