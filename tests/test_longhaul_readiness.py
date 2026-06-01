from jianmu.self_learning.darwinforge.longhaul_symbiote_runner import run_longhaul_symbiote_human_review_fixpack


def test_ready_for_release_false_without_human_review(tmp_path):
    result = run_longhaul_symbiote_human_review_fixpack(tmp_path, ["v0_9_23_reference", "longhaul_redqueen_hydrabudget_symbiote"], compiler_validation_target=4, compile_worker_count=2)
    readiness = result["readiness"]
    assert readiness["ready_for_v1_0_rc1_branch"] is True
    assert readiness["ready_for_v1_0_release"] is False
    assert readiness["human_review_completed"] is False


def test_architecture_charter_guard_still_passes(tmp_path):
    result = run_longhaul_symbiote_human_review_fixpack(tmp_path, ["v0_9_23_reference"], compiler_validation_target=4, compile_worker_count=2)
    assert result["architecture"]["charter_guard_passed"] is True


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("longhaul*.py"))
    assert "import expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("longhaul*.py"))
    assert "openai" not in text.lower()
    assert "requests." not in text.lower()


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("longhaul*.py"))
    assert "keyword_gate" not in text
    assert "keyword rejection gate" not in text


def test_real_promotion_disabled(tmp_path):
    result = run_longhaul_symbiote_human_review_fixpack(tmp_path, ["v0_9_23_reference"], compiler_validation_target=4, compile_worker_count=2)
    assert result["readiness"]["ready_for_v1_0_release"] is False
