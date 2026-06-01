from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_field_ablation import run_field_ablation


def test_mirrorforge_field_ablation_outputs_critical_fields(tmp_path):
    result = run_field_ablation(tmp_path)
    assert result["field_ablation_completed"] is True
    assert "loop_bound_explicit" in result["most_critical_fields"]
    assert "function_signature_detail" in result["removable_fields"]
