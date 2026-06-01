from __future__ import annotations

from typing import Any, Dict, List


TOKEN_VERSION = "mirror_token_v1"
TOKEN_GRAMMAR_ID = "jianmu_mirror_token_bounded_control_v1"

SUPPORTED_CONSTRUCTS = [
    "int_variable",
    "int_constant",
    "assignment",
    "sequence",
    "if_else",
    "bounded_for",
    "bounded_while_fuel",
    "nested_bounded_control",
    "print_int",
    "pure_function_no_recursion_experimental",
    "fixed_array_no_pointer_experimental",
]

UNSUPPORTED_CONSTRUCTS = ["recursion", "pointer", "dynamic_memory", "io", "system_call", "concurrency", "exception", "floating_point"]

TOKEN_VOCAB = [
    "PROGRAM_BEGIN",
    "PROGRAM_END",
    "VAR",
    "INIT",
    "ASSIGN",
    "UPDATE",
    "ADD",
    "SUB",
    "MUL",
    "DIV_SAFE",
    "IF",
    "THEN",
    "ELSE",
    "END_IF",
    "LOOP_FIXED",
    "WHILE_FUEL",
    "END_LOOP",
    "OUTPUT",
    "CONST",
    "NAME",
    "CMP",
    "GT",
    "LT",
    "EQ",
    "FUNC_EXPERIMENTAL",
    "ARRAY_EXPERIMENTAL",
]


def mirror_token_schema() -> Dict[str, Any]:
    return {
        "token_version": TOKEN_VERSION,
        "token_grammar_id": TOKEN_GRAMMAR_ID,
        "token_vocab": TOKEN_VOCAB,
        "supported_constructs": SUPPORTED_CONSTRUCTS,
        "unsupported_constructs": UNSUPPORTED_CONSTRUCTS,
        "lossless_fields": ["program shape", "variable names", "integer constants", "bounded control", "print target"],
        "lossy_fields": ["comments", "source formatting", "natural language wording"],
        "token_to_ast_coverage": 1.0,
    }


def is_raw_target_ir_dump(token_text: str) -> bool:
    text = token_text.strip()
    return text.startswith("{") or '"op"' in text or '"body"' in text
