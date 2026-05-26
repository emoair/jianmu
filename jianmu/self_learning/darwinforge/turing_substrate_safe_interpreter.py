from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class InterpreterConfig:
    max_steps: int = 10_000
    max_abs_value: int = 9_000_000_000_000


class TuringSubstrateError(ValueError):
    pass


def evaluate_program(target_ir: Dict[str, Any], config: InterpreterConfig | None = None) -> str:
    cfg = config or InterpreterConfig()
    env: Dict[str, int] = {}
    output: List[str] = []
    steps = {"count": 0}
    if target_ir.get("op") != "Program":
        raise TuringSubstrateError("root must be Program")
    _exec_block(target_ir.get("body", []), env, output, steps, cfg)
    return "".join(output)


def inspect_program(target_ir: Dict[str, Any]) -> Dict[str, Any]:
    info = {
        "statement_count": 0,
        "expression_count": 0,
        "max_ast_depth": 0,
        "loop_count": 0,
        "max_loop_bound": None,
        "estimated_step_bound": 0,
        "features": {
            "has_variable_decl": False,
            "has_assignment": False,
            "has_sequence": False,
            "has_if_else": False,
            "has_for_loop": False,
            "has_while_loop": False,
            "has_nested_control": False,
            "has_function": False,
            "has_array": False,
            "has_pointer": False,
            "has_recursion": False,
        },
    }

    def walk_stmt(stmt: Dict[str, Any], depth: int, control_depth: int) -> None:
        info["statement_count"] += 1
        info["max_ast_depth"] = max(info["max_ast_depth"], depth)
        op = stmt.get("op")
        if op == "VarDecl":
            info["features"]["has_variable_decl"] = True
            walk_expr(stmt["value"], depth + 1)
        elif op == "Assign":
            info["features"]["has_assignment"] = True
            walk_expr(stmt["value"], depth + 1)
        elif op == "Print":
            walk_expr(stmt["value"], depth + 1)
        elif op == "IfElse":
            info["features"]["has_if_else"] = True
            if control_depth:
                info["features"]["has_nested_control"] = True
            walk_expr(stmt["cond"], depth + 1)
            for child in stmt.get("then", []):
                walk_stmt(child, depth + 1, control_depth + 1)
            for child in stmt.get("else", []):
                walk_stmt(child, depth + 1, control_depth + 1)
        elif op == "ForBounded":
            info["features"]["has_for_loop"] = True
            info["loop_count"] += 1
            bound = int(stmt.get("bound", 0))
            info["max_loop_bound"] = max(info["max_loop_bound"] or 0, bound)
            info["estimated_step_bound"] += bound * max(1, len(stmt.get("body", [])))
            if control_depth:
                info["features"]["has_nested_control"] = True
            for child in stmt.get("body", []):
                walk_stmt(child, depth + 1, control_depth + 1)
        elif op == "WhileBoundedFuel":
            info["features"]["has_while_loop"] = True
            info["loop_count"] += 1
            fuel = int(stmt.get("fuel", 0))
            info["max_loop_bound"] = max(info["max_loop_bound"] or 0, fuel)
            info["estimated_step_bound"] += fuel * max(1, len(stmt.get("body", [])))
            if control_depth:
                info["features"]["has_nested_control"] = True
            walk_expr(stmt["cond"], depth + 1)
            for child in stmt.get("body", []):
                walk_stmt(child, depth + 1, control_depth + 1)

    def walk_expr(expr: Dict[str, Any], depth: int) -> None:
        info["expression_count"] += 1
        info["max_ast_depth"] = max(info["max_ast_depth"], depth)
        if "args" in expr:
            for arg in expr["args"]:
                walk_expr(arg, depth + 1)
        if "arg" in expr:
            walk_expr(expr["arg"], depth + 1)
        if expr.get("op") == "Compare":
            walk_expr(expr["left"], depth + 1)
            walk_expr(expr["right"], depth + 1)

    body = target_ir.get("body", [])
    if len(body) > 1:
        info["features"]["has_sequence"] = True
    for stmt in body:
        walk_stmt(stmt, 1, 0)
    info["estimated_step_bound"] += info["statement_count"]
    return info


def _exec_block(body: List[Dict[str, Any]], env: Dict[str, int], output: List[str], steps: Dict[str, int], cfg: InterpreterConfig) -> None:
    for stmt in body:
        _tick(steps, cfg)
        op = stmt.get("op")
        if op == "VarDecl":
            env[stmt["name"]] = _checked(_eval_expr(stmt["value"], env, cfg), cfg)
        elif op == "Assign":
            if stmt["name"] not in env:
                raise TuringSubstrateError("assignment to undeclared variable")
            env[stmt["name"]] = _checked(_eval_expr(stmt["value"], env, cfg), cfg)
        elif op == "Print":
            output.append(f"{_eval_expr(stmt['value'], env, cfg)}\n")
        elif op == "IfElse":
            _exec_block(stmt.get("then", []) if _eval_cond(stmt["cond"], env, cfg) else stmt.get("else", []), env, output, steps, cfg)
        elif op == "ForBounded":
            name = stmt["var"]
            bound = int(stmt["bound"])
            if bound < 0 or bound > 20:
                raise TuringSubstrateError("for bound outside supported range")
            old = env.get(name)
            for i in range(bound):
                env[name] = i
                _exec_block(stmt.get("body", []), env, output, steps, cfg)
            if old is None:
                env.pop(name, None)
            else:
                env[name] = old
        elif op == "WhileBoundedFuel":
            fuel = int(stmt["fuel"])
            if fuel < 0 or fuel > 20:
                raise TuringSubstrateError("while fuel outside supported range")
            while fuel > 0 and _eval_cond(stmt["cond"], env, cfg):
                _exec_block(stmt.get("body", []), env, output, steps, cfg)
                fuel -= 1
        else:
            raise TuringSubstrateError(f"unsupported statement op: {op}")


def _eval_expr(expr: Dict[str, Any], env: Dict[str, int], cfg: InterpreterConfig) -> int:
    op = expr.get("op")
    if op == "Int":
        return _checked(int(expr["value"]), cfg)
    if op == "Var":
        if expr["name"] not in env:
            raise TuringSubstrateError("unknown variable")
        return env[expr["name"]]
    if op == "Neg":
        return _checked(-_eval_expr(expr["arg"], env, cfg), cfg)
    if op in {"Add", "Sub", "Mul", "DivExact"}:
        left = _eval_expr(expr["args"][0], env, cfg)
        right = _eval_expr(expr["args"][1], env, cfg)
        if op == "Add":
            return _checked(left + right, cfg)
        if op == "Sub":
            return _checked(left - right, cfg)
        if op == "Mul":
            return _checked(left * right, cfg)
        if right == 0 or left % right != 0:
            raise TuringSubstrateError("unsupported division")
        return _checked(left // right, cfg)
    raise TuringSubstrateError(f"unsupported expression op: {op}")


def _eval_cond(cond: Dict[str, Any], env: Dict[str, int], cfg: InterpreterConfig) -> bool:
    if cond.get("op") != "Compare":
        raise TuringSubstrateError("condition must be Compare")
    left = _eval_expr(cond["left"], env, cfg)
    right = _eval_expr(cond["right"], env, cfg)
    cmp = cond["cmp"]
    if cmp == "<":
        return left < right
    if cmp == "<=":
        return left <= right
    if cmp == ">":
        return left > right
    if cmp == ">=":
        return left >= right
    if cmp == "==":
        return left == right
    if cmp == "!=":
        return left != right
    raise TuringSubstrateError("unsupported comparison")


def _tick(steps: Dict[str, int], cfg: InterpreterConfig) -> None:
    steps["count"] += 1
    if steps["count"] > cfg.max_steps:
        raise TuringSubstrateError("step bound exceeded")


def _checked(value: int, cfg: InterpreterConfig) -> int:
    if abs(value) > cfg.max_abs_value:
        raise TuringSubstrateError("overflow risk")
    return value
