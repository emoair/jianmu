from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_ast_to_token import ast_to_mirror_token


def test_mirrorforge_ast_to_token_deterministic() -> None:
    ir = {"op": "Program", "body": [{"op": "VarDecl", "name": "x", "value": {"op": "ConstInt", "value": 3}}, {"op": "PrintInt", "value": {"op": "VarRef", "name": "x"}}]}
    assert ast_to_mirror_token(ir) == ast_to_mirror_token(ir)
