from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_field_ablation import run_field_ablation
from jianmu.self_learning.darwinforge.mirrorforge_robustness_eval import run_robustness_eval
from jianmu.self_learning.darwinforge.mirrorforge_v2_schema_recommendation import recommend_mirrortoken_v2


def test_mirrorforge_v2_schema_recommendation(tmp_path):
    field = run_field_ablation(tmp_path)
    bundle = run_robustness_eval(tmp_path)
    result = recommend_mirrortoken_v2(field, bundle["robustness"], bundle["abstraction_metrics"])
    assert result["ready_for_mirrortoken_v2_schema"] is True
    assert "loop_bound_explicit" in result["critical_fields_to_keep"]
