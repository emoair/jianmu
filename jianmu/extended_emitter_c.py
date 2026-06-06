from typing import List

from jianmu.extended_ir import (
    ArrayProgram,
    ArrayRef,
    Assign,
    BinaryOp,
    CallExpr,
    Expr,
    For,
    FunctionArrayProgram,
    FunctionCallProgram,
    FunctionDecl,
    If,
    IntLiteral,
    Print,
    RecursiveFunctionProgram,
    Return,
    Statement,
    VarDecl,
    VarRef,
    WhileBounded,
)


class ExtendedEmitterC:
    def emit(self, program) -> str:
        if isinstance(program, FunctionCallProgram):
            return self._emit_function_call_program(program)
        if isinstance(program, ArrayProgram):
            return self._emit_array_program(program)
        if isinstance(program, FunctionArrayProgram):
            return self._emit_function_array_program(program)
        if isinstance(program, RecursiveFunctionProgram):
            return self._emit_recursive_program(program)
        raise TypeError("unsupported extended IR program")

    def _emit_function_call_program(self, program: FunctionCallProgram) -> str:
        lines = self._header()
        for fn in program.functions:
            lines.extend(self._function(fn))
            lines.append("")
        lines.extend(["int main(void) {", '    printf("%d\\n", ' + self._expr(program.call) + ");", "    return 0;", "}"])
        return "\n".join(lines) + "\n"

    def _emit_array_program(self, program: ArrayProgram) -> str:
        values = ", ".join(str(int(v)) for v in program.values)
        lines = self._header()
        lines.append("int main(void) {")
        lines.append(f"    int {program.array_name}[{len(program.values)}] = {{{values}}};")
        for stmt in program.body:
            lines.extend(self._stmt(stmt, 1))
        lines.extend(["    return 0;", "}"])
        return "\n".join(lines) + "\n"

    def _emit_function_array_program(self, program: FunctionArrayProgram) -> str:
        values = ", ".join(str(int(v)) for v in program.values)
        lines = self._header()
        for fn in program.functions:
            lines.extend(self._function(fn))
            lines.append("")
        lines.append("int main(void) {")
        lines.append(f"    int {program.array_name}[{len(program.values)}] = {{{values}}};")
        lines.append('    printf("%d\\n", ' + self._expr(program.call) + ");")
        lines.extend(["    return 0;", "}"])
        return "\n".join(lines) + "\n"

    def _emit_recursive_program(self, program: RecursiveFunctionProgram) -> str:
        lines = self._header()
        lines.extend(self._function(program.function))
        lines.append("")
        lines.extend(["int main(void) {", '    printf("%d\\n", ' + self._expr(program.call) + ");", "    return 0;", "}"])
        return "\n".join(lines) + "\n"

    def _function(self, fn: FunctionDecl) -> List[str]:
        prefix = "static " if fn.static else ""
        params = ", ".join("int " + name for name in fn.params)
        lines = [f"{prefix}{fn.return_type} {fn.name}({params}) {{"]
        for stmt in fn.body:
            lines.extend(self._stmt(stmt, 1))
        lines.append("}")
        return lines

    def _stmt(self, stmt: Statement, indent: int) -> List[str]:
        pad = "    " * indent
        if isinstance(stmt, VarDecl):
            return [f"{pad}{stmt.type} {stmt.name} = {self._expr(stmt.init)};"]
        if isinstance(stmt, Assign):
            return [f"{pad}{self._assign_target(stmt.target)} = {self._expr(stmt.value)};"]
        if isinstance(stmt, Return):
            return [f"{pad}return {self._expr(stmt.value)};"]
        if isinstance(stmt, Print):
            return [f'{pad}printf("%d\\n", {self._expr(stmt.value)});']
        if isinstance(stmt, If):
            lines = [f"{pad}if ({self._expr(stmt.condition)}) {{"]
            for child in stmt.then_body:
                lines.extend(self._stmt(child, indent + 1))
            lines.append(f"{pad}}} else {{")
            for child in stmt.else_body:
                lines.extend(self._stmt(child, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(stmt, For):
            v = stmt.var_name
            lines = [f"{pad}for (int {v} = {self._expr(stmt.start)}; {v} < {self._expr(stmt.stop_exclusive)}; {v}++) {{"]
            for child in stmt.body:
                lines.extend(self._stmt(child, indent + 1))
            lines.append(f"{pad}}}")
            return lines
        if isinstance(stmt, WhileBounded):
            fuel_name = f"fuel_{indent}"
            lines = [f"{pad}int {fuel_name} = {int(stmt.fuel)};", f"{pad}while (({self._expr(stmt.condition)}) && {fuel_name} > 0) {{"]
            for child in stmt.body:
                lines.extend(self._stmt(child, indent + 1))
            lines.append(f"{pad}    {fuel_name}--;")
            lines.append(f"{pad}}}")
            return lines
        raise TypeError("unsupported statement")

    def _expr(self, expr: Expr) -> str:
        if isinstance(expr, IntLiteral):
            return str(int(expr.value))
        if isinstance(expr, VarRef):
            return expr.name
        if isinstance(expr, BinaryOp):
            return f"({self._expr(expr.left)} {expr.op} {self._expr(expr.right)})"
        if isinstance(expr, CallExpr):
            return f"{expr.function_name}(" + ", ".join(self._expr(arg) for arg in expr.args) + ")"
        if isinstance(expr, ArrayRef):
            return f"{expr.array_name}[{self._expr(expr.index)}]"
        raise TypeError("unsupported expression")

    def _assign_target(self, expr: Expr) -> str:
        if isinstance(expr, (VarRef, ArrayRef)):
            return self._expr(expr)
        raise TypeError("unsupported assignment target")

    def _header(self) -> List[str]:
        return ["#include <stdio.h>", ""]

