from jianmu.self_learning.darwinforge.opt_true8h_readiness import build_opt_true8h_readiness


def test_opt_true8h_readiness_keeps_production_false(tmp_path) -> None:
    readiness = build_opt_true8h_readiness(tmp_path, {"opt_display_smoke_gate_passed": True, "true8h_backend_validation_passed": True})
    assert readiness["production_function_support_completed"] is False
    assert readiness["production_array_support_completed"] is False
    assert readiness["production_recursion_support_completed"] is False
    assert readiness["real_promotion_enabled"] is False
