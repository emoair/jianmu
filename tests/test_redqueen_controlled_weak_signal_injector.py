from jianmu.self_learning.darwinforge.redqueen_controlled_weak_signal_injector import inject_controlled_weak_signals
from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import build_weak_signal_scenarios


def _plan():
    return {"category_weights": {"function": 1.0, "mixed": 1.0}, "difficulty_levels": {"function": 2}, "active_review_allocations": {"function": 1.0}, "shape_diversity_targets": {}, "replay_recheck_targets": {}, "boundary_recheck_targets": {}}


def test_controlled_weak_signal_injector_marks_synthetic():
    result = inject_controlled_weak_signals(_plan(), build_weak_signal_scenarios(), ["function_call_weak_signal"])
    assert result["weak_signal_is_synthetic"] is True
    assert result["weak_signal_affected_real_correctness"] is False
    assert result["plan"]["category_weights"]["function"] > 1.0


def test_controlled_weak_signal_does_not_affect_real_compile_lane():
    result = inject_controlled_weak_signals(_plan(), build_weak_signal_scenarios(), ["mixed_integration_weak_signal"])
    assert result["injections"][0]["affects_real_compiler"] is False
    assert result["injections"][0]["affects_real_correctness"] is False
