import json

from jianmu.self_learning.darwinforge.redqueen_metrics_bus import build_redqueen_metrics_bus


def test_redqueen_metrics_bus_is_read_only(tmp_path):
    (tmp_path / "v1_0_8_controlled_support").mkdir()
    (tmp_path / "v1_0_7_2_coverage_replay").mkdir()
    (tmp_path / "v1_0_8_controlled_support" / "controlled_opt_in_support_readiness.json").write_text(json.dumps({"compiler_verified_correctness_rate": 1.0, "positive_validation_events": 60000}), encoding="utf-8")
    (tmp_path / "v1_0_7_2_coverage_replay" / "coverage_expansion_readiness.json").write_text(json.dumps({"new_source_sha256_unique_count": 50888}), encoding="utf-8")
    result = build_redqueen_metrics_bus(tmp_path, tmp_path / "out")
    assert result["metrics_bus_read_only"] is True
    assert result["no_model_training"] is True
