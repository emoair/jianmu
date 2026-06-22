from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import (
    RedQueenWeakSignalConfig,
    build_controlled_weak_signal_design,
    build_multiround_config_record,
    build_weak_signal_scenarios,
)


def test_redqueen_weak_signal_schema():
    design = build_controlled_weak_signal_design()
    scenarios = build_weak_signal_scenarios()
    config = build_multiround_config_record(RedQueenWeakSignalConfig())
    assert design["weak_signal_design_passed"] is True
    assert design["weak_signal_affects_real_correctness"] is False
    assert len(scenarios) >= 3
    assert all(item["weak_signal_is_synthetic"] for item in scenarios)
    assert config["cycles"] == 5
