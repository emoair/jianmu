from jianmu.extended_ir import (
    ArrayProgram,
    ArrayRef,
    BinaryOp,
    CallExpr,
    Expr,
    FunctionArrayProgram,
    FunctionCallProgram,
    FunctionDecl,
    IntLiteral,
    RecursiveFunctionProgram,
    Statement,
    VarRef,
)


def test_extended_ir_contains_function_array_recursion_nodes():
    assert issubclass(IntLiteral, Expr)
    assert issubclass(VarRef, Expr)
    assert issubclass(BinaryOp, Expr)
    assert issubclass(CallExpr, Expr)
    assert issubclass(ArrayRef, Expr)
    assert FunctionDecl("f", ["x"], []).name == "f"
    assert FunctionCallProgram([], CallExpr("f", [])).experimental_active_path is True
    assert ArrayProgram("a", [1], []).production_supported is False
    assert FunctionArrayProgram([], "a", [1], CallExpr("f", [])).production_supported is False
    assert RecursiveFunctionProgram(FunctionDecl("f", ["x"], []), CallExpr("f", [])).production_recursion_support is False
    assert Statement is not None

