from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.mirrorforge_token_schema import TOKEN_GRAMMAR_ID, TOKEN_VERSION, TOKEN_VOCAB


def ast_to_mirror_token(target_ir: Dict[str, Any]) -> Dict[str, Any]:
    sequence = ["PROGRAM_BEGIN"]
    for stmt in target_ir.get("body", []):
        sequence.extend(_stmt_tokens(stmt))
    sequence.append("PROGRAM_END")
    text = " ".join(sequence)
    return {
        "token_version": TOKEN_VERSION,
        "token_sequence": sequence,
        "token_text": text,
        "token_vocab": sorted(set(sequence).union({"PROGRAM_BEGIN", "PROGRAM_END"})),
        "token_grammar_id": TOKEN_GRAMMAR_ID,
        "reversible_to_ir": True,
        "lossy_fields": ["comments", "formatting"],
        "token_hash": _hash(text),
        "source_ast_hash": _hash(json.dumps(target_ir, ensure_ascii=False, sort_keys=True)),
    }


def _stmt_tokens(stmt: Dict[str, Any]) -> List[str]:
    op = stmt.get("op")
    if op == "VarDecl":
        return ["VAR", str(stmt["name"]), "INIT", *_expr_tokens(stmt["value"])]
    if op == "Assign":
        return ["ASSIGN", str(stmt["name"]), *_expr_tokens(stmt["value"])]
    if op == "PrintInt":
        return ["OUTPUT", *_expr_tokens(stmt["value"])]
    if op == "ForRange":
        body = ["LOOP_FIXED", str(stmt.get("count", 1))]
        for child in stmt.get("body", []):
            body.extend(_stmt_tokens(child))
        body.append("END_LOOP")
        return body
    if op == "IfElse":
        out = ["IF", *_expr_tokens(stmt["condition"]), "THEN"]
        for child in stmt.get("then_body", []):
            out.extend(_stmt_tokens(child))
        if stmt.get("else_body"):
            out.append("ELSE")
            for child in stmt.get("else_body", []):
                out.extend(_stmt_tokens(child))
        out.append("END_IF")
        return out
    return ["UNSUPPORTED_STMT", str(op)]


def _expr_tokens(expr: Dict[str, Any]) -> List[str]:
    op = expr.get("op")
    if op == "ConstInt":
        return ["CONST", str(expr["value"])]
    if op == "VarRef":
        return ["NAME", str(expr["name"])]
    if op == "BinaryOp":
        op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV_SAFE"}
        return [op_map.get(expr.get("operator"), "OP"), *_expr_tokens(expr["left"]), *_expr_tokens(expr["right"])]
    if op == "CompareOp":
        cmp_map = {">": "GT", "<": "LT", "==": "EQ"}
        return ["CMP", cmp_map.get(expr.get("operator"), "CMP_OP"), *_expr_tokens(expr["left"]), *_expr_tokens(expr["right"])]
    return ["UNSUPPORTED_EXPR", str(op)]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
