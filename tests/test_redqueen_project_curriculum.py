from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_project_curriculum import build_redqueen_project_curriculum


def test_redqueen_project_curriculum_shadow_only() -> None:
    result = build_redqueen_project_curriculum()
    assert result["targeted_project_curriculum_enabled"] is True
    assert result["real_promotion_enabled"] is False

