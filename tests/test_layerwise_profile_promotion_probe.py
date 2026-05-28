from jianmu.self_learning.darwinforge.layerwise_profile_promotion_probe import run_layerwise_profile_promotion_probe


def test_layerwise_profile_promotion_probe_shadow_only(tmp_path):
    source = tmp_path / "source"
    base = tmp_path / "base"
    source.mkdir()
    base.mkdir()
    (source / "layerwise_compiler_readiness.json").write_text("{}", encoding="utf-8")
    (base / "adaptive_layerwise_metrics.json").write_text("{}", encoding="utf-8")
    out = tmp_path / "out"
    result = run_layerwise_profile_promotion_probe(tmp_path, source, base, out, profiles=["current_1B_reference"], samples=0, boundary_samples=0, run_compiler_validation=False, run_cross_process=False)
    assert result["readiness"]["real_promotion_enabled"] is False
    assert result["readiness"]["profile_is_default_runtime"] is False
