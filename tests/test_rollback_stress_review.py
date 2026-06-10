from jianmu.self_learning.darwinforge.rollback_stress_review import run_rollback_stress_review


def test_rollback_stress_review_keeps_default_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.rollback_stress_review.execute_shadow_profile_request",
        lambda *args, **kwargs: {"passed": True, "real_promotion_enabled": False, "production_profile_modified": False},
    )
    monkeypatch.setattr(
        "jianmu.self_learning.darwinforge.rollback_stress_review.execute_with_backend",
        lambda *args, **kwargs: {"stdout_value_if_safe": 3},
    )
    result = run_rollback_stress_review(tmp_path, rollback_cycles=1, samples_per_cycle=1)
    assert result["default_profile_after_each_cycle_unchanged"] is True
    assert result["production_flags_after_each_cycle_false"] is True
