from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_autopsy import load_inputs
from jianmu.self_learning.darwinforge.redqueen_template_overfit_audit import audit_redqueen_template_overfit


def test_template_overfit_audit_detects_concentration() -> None:
    data = load_inputs("records/v0_9_17", "records/v0_9_18", "records/v0_9_18_2", "datasets/v0_9_17_redqueen_curriculum")
    result = audit_redqueen_template_overfit(data)
    assert "template_family_concentration_top1" in result
    assert result["pseudo_diversity_score"] >= 0.70
    assert result["severe_template_collapse_detected"] is False
