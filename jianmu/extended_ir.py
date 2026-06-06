from dataclasses import dataclass, field
from typing import List, Optional


class Expr:
    pass


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class VarRef(Expr):
    name: str


@dataclass
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class CallExpr(Expr):
    function_name: str
    args: List[Expr] = field(default_factory=list)


@dataclass
class ArrayRef(Expr):
    array_name: str
    index: Expr


class Statement:
    pass


@dataclass
class VarDecl(Statement):
    name: str
    init: Expr
    type: str = "int"


@dataclass
class Assign(Statement):
    target: Expr
    value: Expr


@dataclass
class Return(Statement):
    value: Expr


@dataclass
class Print(Statement):
    value: Expr


@dataclass
class If(Statement):
    condition: Expr
    then_body: List[Statement] = field(default_factory=list)
    else_body: List[Statement] = field(default_factory=list)


@dataclass
class For(Statement):
    var_name: str
    start: Expr
    stop_exclusive: Expr
    body: List[Statement] = field(default_factory=list)


@dataclass
class WhileBounded(Statement):
    condition: Expr
    fuel: int
    body: List[Statement] = field(default_factory=list)


@dataclass
class FunctionDecl:
    name: str
    params: List[str]
    body: List[Statement]
    return_type: str = "int"
    static: bool = True


@dataclass
class FunctionCallProgram:
    functions: List[FunctionDecl]
    call: CallExpr
    expected_stdout: Optional[str] = None
    production_supported: bool = False
    experimental_active_path: bool = True


@dataclass
class ArrayProgram:
    array_name: str
    values: List[int]
    body: List[Statement]
    expected_stdout: Optional[str] = None
    production_supported: bool = False
    experimental_active_path: bool = True


@dataclass
class FunctionArrayProgram:
    functions: List[FunctionDecl]
    array_name: str
    values: List[int]
    call: CallExpr
    expected_stdout: Optional[str] = None
    production_supported: bool = False
    experimental_active_path: bool = True


@dataclass
class RecursiveFunctionProgram:
    function: FunctionDecl
    call: CallExpr
    recursion_mode: str = "bounded_structural_recursion_validation"
    max_depth: int = 12
    expected_stdout: Optional[str] = None
    production_recursion_support: bool = False
    production_supported: bool = False
    experimental_active_path: bool = True

