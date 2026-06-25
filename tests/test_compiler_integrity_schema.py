from jianmu.self_learning.darwinforge.compiler_integrity_schema import BACKEND_POLICIES, BackendValidationConfig


def test_compiler_integrity_schema() -> None:
    cfg = BackendValidationConfig()
    assert cfg.minimum_backend_cl_invocations == 15000
    assert "structured_recursion" in BACKEND_POLICIES

