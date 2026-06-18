from jianmu.self_learning.darwinforge.controlled_opt_in_approval_readiness import build_controlled_opt_in_approval_readiness


def test_controlled_opt_in_approval_readiness_keeps_production_false(tmp_path):
    verdict = {
        "approval_status": "approval_recommended",
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_official_release": False,
    }
    isolation = {"isolation_fix_applied": True, "tests_write_real_records_detected": False, "historical_records_write_detected": True}
    result = build_controlled_opt_in_approval_readiness(tmp_path, verdict, isolation)
    assert result["recommended_claim_level"] == "controlled_opt_in_support_approval_recommended"
    assert result["production_function_support_completed"] is False
    assert result["ready_for_official_release"] is False


def test_no_external_api_calls():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/approval_gate_verdict.py").read_text(encoding="utf-8")
    assert "openai" not in text.lower()
    assert "requests." not in text


def test_real_promotion_disabled():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/approval_gate_verdict.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": True' not in text
