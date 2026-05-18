import copy
import string
from jianmu.ir import ProgramIR, Variable, SumExpression


class IncludeExpert:
    def apply(self, ir: ProgramIR) -> ProgramIR:
        ir = copy.deepcopy(ir)
        if "stdio.h" not in ir.includes:
            ir.includes.append("stdio.h")
        return ir


class VariableDefinitionExpert:
    def __init__(self, var_count: int, values: list = None):
        self.var_count = var_count
        self.values = values or [1] * var_count

    def apply(self, ir: ProgramIR) -> ProgramIR:
        ir = copy.deepcopy(ir)
        names = list(string.ascii_lowercase)
        vals = self.values + [1] * max(0, self.var_count - len(self.values))
        ir.variables = [Variable(name=names[i], value=vals[i]) for i in range(self.var_count)]
        return ir


class SumExpressionExpert:
    def apply(self, ir: ProgramIR) -> ProgramIR:
        ir = copy.deepcopy(ir)
        ir.expression = SumExpression(operands=[v.name for v in ir.variables])
        return ir


class PrintfExpert:
    def apply(self, ir: ProgramIR) -> ProgramIR:
        ir = copy.deepcopy(ir)
        ir.print = True
        return ir


class MainFunctionExpert:
    def apply(self, ir: ProgramIR) -> ProgramIR:
        ir = copy.deepcopy(ir)
        ir.return_code = 0
        return ir


class ExpandSumExpert:
    def __init__(self, target_count: int, new_value: int = 1):
        if target_count < 1:
            raise ValueError(f"target_count must be >= 1, got {target_count}")
        self.target_count = target_count
        self.new_value = new_value

    def apply(self, ir: ProgramIR) -> ProgramIR:
        ir = copy.deepcopy(ir)
        names = list(string.ascii_lowercase)
        current = len(ir.variables)
        if self.target_count > current:
            # Expand: append new variables with new_value
            for i in range(current, self.target_count):
                ir.variables.append(Variable(name=names[i], value=self.new_value))
        else:
            # Reduce: trim to target
            ir.variables = ir.variables[:self.target_count]
        ir.expression.operands = [v.name for v in ir.variables]
        return ir


class ConsistencyCheckExpert:
    def apply(self, ir: ProgramIR) -> ProgramIR:
        defined = {v.name for v in ir.variables}
        for name in ir.expression.operands:
            if name not in defined:
                raise ValueError(f"Variable '{name}' in expression not defined in variables")
        return ir
