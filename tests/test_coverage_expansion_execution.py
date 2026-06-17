from jianmu.self_learning.darwinforge.coverage_expansion_execution import _blocked_row, execute_coverage_sample
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend


def test_coverage_expansion_execution_blocking_row_keeps_default_closed():
    row = _blocked_row(1, "default_blocking", "profile", "default_profile_blocking_check", "flag", "explicit_opt_in_required")
    assert row["passed"] is True
    assert row["default_profile_modified"] is False
    assert row["real_promotion_enabled"] is False


def test_coverage_expansion_execution_noncompiler_environment_is_not_stubbed():
    backend = CompilerBackend("missing", "", "")
    row = execute_coverage_sample(1, "function", backend, "profile")
    assert row["compiler_invoked"] is False
    assert row["stubbed"] is False
