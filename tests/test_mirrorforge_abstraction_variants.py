from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_abstraction_variants import build_abstraction_variant_dataset, make_variant_token
from jianmu.self_learning.darwinforge.mirrorforge_ast_to_token import ast_to_mirror_token


def test_mirrorforge_abstraction_variants_generated(tmp_path):
    source = tmp_path / "source"
    from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset

    build_mirrorforge_dataset(source, minimum_samples=10, counts_by_scale={"pilot": 10})
    summary = build_abstraction_variant_dataset(source, tmp_path / "variants", variants=["lossless", "semantic"])
    assert summary["abstraction_variants_generated"] is True
    assert summary["variant_count"] == 2
    assert (tmp_path / "variants" / "semantic_mirror_token" / "manifest.json").exists()


def test_mirrorforge_semantic_token_not_raw_target_ir():
    token = ast_to_mirror_token({"op": "Program", "body": [{"op": "VarDecl", "name": "x", "value": {"op": "ConstInt", "value": 3}}]})
    semantic = make_variant_token(token, "semantic")
    assert semantic["is_raw_target_ir_dump"] is False
    assert '"op"' not in semantic["token_text"]
    assert "INTRODUCE_SLOT" in semantic["token_sequence"]
