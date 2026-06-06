from __future__ import annotations

from jianmu.extended_ir import BinaryOp, CallExpr, FunctionDecl, If, IntLiteral, RecursiveFunctionProgram, Return, VarRef
from jianmu.self_learning.darwinforge.turing_frontier_schema import recursion_contract


def build_factorial_program(n: int = 5) -> RecursiveFunctionProgram:
    contract = recursion_contract()
    fn = FunctionDecl(
        name="fact",
        params=["n"],
        body=[
            If(
                BinaryOp("<=", VarRef("n"), IntLiteral(1)),
                [Return(IntLiteral(1))],
                [Return(BinaryOp("*", VarRef("n"), CallExpr("fact", [BinaryOp("-", VarRef("n"), IntLiteral(1))])))],
            )
        ],
    )
    expected = _fact(n)
    return RecursiveFunctionProgram(
        function=fn,
        call=CallExpr("fact", [IntLiteral(n)]),
        max_depth=n + 1,
        expected_stdout=f"{expected}\n",
        production_recursion_support=bool(contract.get("production_supported", False)),
    )


def _fact(n: int) -> int:
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

