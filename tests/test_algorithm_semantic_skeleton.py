from jianmu.self_learning.darwinforge.algorithm_semantic_skeleton import build_semantic_skeleton


def test_algorithm_semantic_skeleton_contains_required_fields():
    skeleton = build_semantic_skeleton(0)
    assert skeleton["base_skeleton_id"]
    assert skeleton["semantic_skeleton_hash"]
    assert "algorithm_family" in skeleton
    assert "supported_variant_axes" in skeleton
