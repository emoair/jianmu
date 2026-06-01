from __future__ import annotations

from jianmu.self_learning.darwinforge.codecartographer_roundtrip_eval import run_codecartographer_roundtrip_eval


def test_codecartographer_roundtrip_eval(tmp_path):
    result = run_codecartographer_roundtrip_eval(tmp_path)
    assert result["module_to_token_success_rate"] >= 0.95
    assert result["unsupported_feature_misroute_count"] == 0
