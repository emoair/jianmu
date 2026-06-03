from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy_clean_rerun import run_v0_9_27_1


def test_ready_for_release_false(tmp_path, monkeypatch):
    import jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy_clean_rerun as runner

    monkeypatch.setattr(runner, "run_clean_validation", lambda *a, **k: {
        "full_compile_invocation_count": 20000,
        "compiler_verified_correctness_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "validation_clean": True,
    })
    result = run_v0_9_27_1("records/v0_9_27", tmp_path / "records", tmp_path / "dataset", target_samples=1000, minimum_samples=1000, full_compile_target=2, wall_clock_min_hours=0.0, max_runtime_hours=0.0)
    assert result["readiness"]["ready_for_v1_0_release"] is False
    assert result["readiness"]["ready_for_function_array_frontier_review"] is True


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*batch*compile*.py"))
    assert "import expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*batch*compile*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*batch*compile*.py"))
    assert "keyword rejection gate" not in text


def test_real_promotion_disabled(tmp_path, monkeypatch):
    import jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy_clean_rerun as runner

    monkeypatch.setattr(runner, "run_clean_validation", lambda *a, **k: {
        "full_compile_invocation_count": 20000,
        "compiler_verified_correctness_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "validation_clean": True,
    })
    result = run_v0_9_27_1("records/v0_9_27", tmp_path / "records", tmp_path / "dataset", target_samples=1000, minimum_samples=1000, full_compile_target=2, wall_clock_min_hours=0.0, max_runtime_hours=0.0)
    assert result["readiness"]["ready_for_v1_0_release"] is False
