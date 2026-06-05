from jianmu.self_learning.darwinforge.redqueen_linguaforge_wide_boundary_curriculum import redqueen_curriculum


def test_redqueen_linguaforge_wide_boundary_curriculum_assignments():
    curriculum = redqueen_curriculum()
    assert "nl_algorithm_requirement_assignment" in curriculum
    assert "bidirectional_alignment_assignment" in curriculum
    assert all("token bypass" in " ".join(v["forbidden_features"]) for v in curriculum.values())
