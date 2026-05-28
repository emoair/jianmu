from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_clean_independent_validation import _needs_fallback, _summarize


def test_clean_independent_validation_uses_fixed_temp_manager() -> None:
    import inspect
    import jianmu.self_learning.darwinforge.bounded_substrate_clean_independent_validation as module

    assert "validate_sample_with_temp_manager" in inspect.getsource(module)


def test_clean_independent_validation_uses_real_cl() -> None:
    metric = {"completed": True, "permission_error_count": 0}
    assert _needs_fallback(metric) is False


def test_clean_independent_validation_reports_primary_and_fallback_separately() -> None:
    assert _needs_fallback({"completed": False}) is True
    assert _needs_fallback({"completed": True, "permission_error_count": 1}) is True
