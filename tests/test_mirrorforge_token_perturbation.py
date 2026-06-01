from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_ast_to_token import ast_to_mirror_token
from jianmu.self_learning.darwinforge.mirrorforge_token_perturbation import perturb_mirror_token


def test_mirrorforge_token_perturbation_preserves_semantics():
    token = ast_to_mirror_token({"op": "Program", "body": [{"op": "PrintInt", "value": {"op": "ConstInt", "value": 7}}]})
    perturbed = perturb_mirror_token(token, "synonym_token_replacement")
    assert perturbed["semantic_preserving"] is True
    assert perturbed["normalized_token_sequence"] == token["token_sequence"]
