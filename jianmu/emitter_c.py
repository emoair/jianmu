from jianmu.ir import ProgramIR


class CEmitter:
    def emit(self, ir: ProgramIR) -> str:
        lines = []
        for inc in ir.includes:
            lines.append(f"#include <{inc}>")
        lines.append("")
        lines.append("int main(void) {")
        for v in ir.variables:
            lines.append(f"    {v.type} {v.name} = {v.value};")
        if ir.print and ir.expression.operands:
            expr = " + ".join(ir.expression.operands)
            lines.append(f'    printf("%d\\n", {expr});')
        lines.append(f"    return {ir.return_code};")
        lines.append("}")
        return "\n".join(lines) + "\n"
