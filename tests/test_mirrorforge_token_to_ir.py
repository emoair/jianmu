from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_ast_to_token import ast_to_mirror_token
from jianmu.self_learning.darwinforge.mirrorforge_token_to_ir import mirror_token_to_ir


def test_mirrorforge_token_to_ir_roundtrip() -> None:
    ir = {"op": "Program", "body": [{"op": "VarDecl", "name": "x", "value": {"op": "ConstInt", "value": 7}}, {"op": "PrintInt", "value": {"op": "VarRef", "name": "x"}}]}
    assert mirror_token_to_ir(ast_to_mirror_token(ir)) == ir
