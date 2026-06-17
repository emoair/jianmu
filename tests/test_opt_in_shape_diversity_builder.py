from jianmu.self_learning.darwinforge.opt_in_shape_diversity_builder import build_expanded_shape


def test_shape_diversity_builder_expands_function_shapes():
    a = build_expanded_shape("function", 210)
    b = build_expanded_shape("function", 211)
    assert a["shape_signature"] != b["shape_signature"]
    assert "static int" in a["source"]


def test_shape_diversity_builder_expands_array_shapes():
    a = build_expanded_shape("array", 210)
    b = build_expanded_shape("array", 211)
    assert a["source_sha256"] if "source_sha256" in a else a["source"] != b["source"]
    assert "for (int i" in a["source"]
