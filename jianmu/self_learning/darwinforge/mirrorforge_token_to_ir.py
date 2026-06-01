from __future__ import annotations

from typing import Any, Dict, List, Tuple


def mirror_token_to_ir(mirror_token: Dict[str, Any]) -> Dict[str, Any]:
    tokens = list(mirror_token["token_sequence"])
    if not tokens or tokens[0] != "PROGRAM_BEGIN" or tokens[-1] != "PROGRAM_END":
        raise ValueError("invalid mirror token program bounds")
    body: List[Dict[str, Any]] = []
    index = 1
    while index < len(tokens) - 1:
        stmt, index = _parse_stmt(tokens, index)
        body.append(stmt)
    return {"op": "Program", "body": body}


def _parse_stmt(tokens: List[str], index: int) -> Tuple[Dict[str, Any], int]:
    head = tokens[index]
    if head == "VAR":
        name = tokens[index + 1]
        if tokens[index + 2] != "INIT":
            raise ValueError("VAR missing INIT")
        expr, nxt = _parse_expr(tokens, index + 3)
        return {"op": "VarDecl", "name": name, "value": expr}, nxt
    if head == "ASSIGN":
        name = tokens[index + 1]
        expr, nxt = _parse_expr(tokens, index + 2)
        return {"op": "Assign", "name": name, "value": expr}, nxt
    if head == "OUTPUT":
        expr, nxt = _parse_expr(tokens, index + 1)
        return {"op": "PrintInt", "value": expr}, nxt
    if head == "LOOP_FIXED":
        count = int(tokens[index + 1])
        body: List[Dict[str, Any]] = []
        index += 2
        while tokens[index] != "END_LOOP":
            stmt, index = _parse_stmt(tokens, index)
            body.append(stmt)
        return {"op": "ForRange", "count": count, "body": body}, index + 1
    if head == "IF":
        condition, index = _parse_expr(tokens, index + 1)
        if tokens[index] != "THEN":
            raise ValueError("IF missing THEN")
        index += 1
        then_body: List[Dict[str, Any]] = []
        else_body: List[Dict[str, Any]] = []
        active = then_body
        while tokens[index] != "END_IF":
            if tokens[index] == "ELSE":
                active = else_body
                index += 1
                continue
            stmt, index = _parse_stmt(tokens, index)
            active.append(stmt)
        return {"op": "IfElse", "condition": condition, "then_body": then_body, "else_body": else_body}, index + 1
    raise ValueError(f"unsupported token statement: {head}")


def _parse_expr(tokens: List[str], index: int) -> Tuple[Dict[str, Any], int]:
    head = tokens[index]
    if head == "CONST":
        return {"op": "ConstInt", "value": int(tokens[index + 1])}, index + 2
    if head == "NAME":
        return {"op": "VarRef", "name": tokens[index + 1]}, index + 2
    if head in {"ADD", "SUB", "MUL", "DIV_SAFE"}:
        left, nxt = _parse_expr(tokens, index + 1)
        right, nxt = _parse_expr(tokens, nxt)
        return {"op": "BinaryOp", "operator": {"ADD": "+", "SUB": "-", "MUL": "*", "DIV_SAFE": "/"}[head], "left": left, "right": right}, nxt
    if head == "CMP":
        operator = { "GT": ">", "LT": "<", "EQ": "==" }[tokens[index + 1]]
        left, nxt = _parse_expr(tokens, index + 2)
        right, nxt = _parse_expr(tokens, nxt)
        return {"op": "CompareOp", "operator": operator, "left": left, "right": right}, nxt
    raise ValueError(f"unsupported token expression: {head}")
