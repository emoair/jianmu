from jianmu.self_learning.darwinforge.redqueen_multiround_stability_schema import RedQueenStabilityConfig, build_multiround_stability_config_record


def test_redqueen_multiround_stability_schema():
    record = build_multiround_stability_config_record(RedQueenStabilityConfig())
    assert record["cycles"] == 8
    assert record["msvc_preflight_required"] is True
    assert "cycle_6" in record["weak_signal_schedule"]
