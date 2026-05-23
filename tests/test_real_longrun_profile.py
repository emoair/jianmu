from jianmu.self_learning.darwinforge.real_longrun_profile import RealLongrunProfiler


def test_real_longrun_profile_runtime_plausibility():
    profile = RealLongrunProfiler().to_dict(total_eval_samples=1, total_external_samples=1)
    assert profile["runtime_plausibility_passed"] is True
    assert profile["peak_memory_mb"] == "unavailable"
