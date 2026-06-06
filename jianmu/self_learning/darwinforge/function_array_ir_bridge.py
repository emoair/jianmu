from __future__ import annotations

from typing import Any, Dict

from jianmu.extended_ir import (
    ArrayProgram,
    ArrayRef,
    Assign,
    BinaryOp,
    CallExpr,
    For,
    FunctionArrayProgram,
    FunctionCallProgram,
    FunctionDecl,
    IntLiteral,
    Print,
    Return,
    VarDecl,
    VarRef,
)
from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import make_forgefrontier_sample


def forgefrontier_row_to_extended_ir(row: Dict[str, Any]):
    """Adapt ForgeFrontier semantics into ExtendedIR; do not reuse its template renderer."""
    target = row.get("target_ir") or {}
    value = int(target.get("stdout", row.get("value", 7)))
    kind = target.get("kind") or row.get("kind")
    if kind == "forge_array":
        return build_array_program(value)
    if kind == "forge_function_array":
        return build_function_array_program(value)
    return build_function_program(value)


def sample_function_ir(index: int = 0):
    return forgefrontier_row_to_extended_ir(make_forgefrontier_sample(index, "pilot"))


def sample_array_ir(index: int = 20):
    return forgefrontier_row_to_extended_ir(make_forgefrontier_sample(index, "pilot"))


def sample_function_array_ir(index: int = 70):
    return forgefrontier_row_to_extended_ir(make_forgefrontier_sample(index, "pilot"))


def build_function_program(value: int) -> FunctionCallProgram:
    fn = FunctionDecl(
        name="calc",
        params=["x"],
        body=[Return(BinaryOp("+", VarRef("x"), IntLiteral(1)))],
    )
    return FunctionCallProgram([fn], CallExpr("calc", [IntLiteral(value - 1)]), expected_stdout=f"{value}\n")


def build_array_program(value: int) -> ArrayProgram:
    values = [value - 3, 1, 1, 1]
    body = [
        VarDecl("s", IntLiteral(0)),
        For("i", IntLiteral(0), IntLiteral(4), [
            Assign(VarRef("s"), BinaryOp("+", VarRef("s"), ArrayRef("a", VarRef("i"))))
        ]),
        Print(VarRef("s")),
    ]
    return ArrayProgram("a", values, body, expected_stdout=f"{value}\n")


def build_function_array_program(value: int) -> FunctionArrayProgram:
    fn = FunctionDecl(
        name="sum3",
        params=["a[]"],
        body=[
            VarDecl("s", IntLiteral(0)),
            For("i", IntLiteral(0), IntLiteral(3), [
                Assign(VarRef("s"), BinaryOp("+", VarRef("s"), ArrayRef("a", VarRef("i"))))
            ]),
            Return(VarRef("s")),
        ],
        return_type="int",
    )
    program = FunctionArrayProgram([fn], "a", [value - 2, 1, 1], CallExpr("sum3", [VarRef("a")]), expected_stdout=f"{value}\n")
    return program
