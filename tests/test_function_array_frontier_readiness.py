import jianmu.self_learning.darwinforge.turing_proof_function_array_frontend_scaleup as scaleup


def _run_quick(tmp_path, monkeypatch, **kwargs):
    def fake_frontend(output_records, target=2):
        return {
            "syntax_frontend_enabled": True,
            "syntax_frontend_checked_count": target,
            "syntax_frontend_pass_count": target,
            "syntax_frontend_fail_count": 0,
            "syntax_frontend_pass_rate": 1.0,
            "syntax_filter_used_as_correctness_evidence": False,
            "process_spawn_failure_count": 0,
            "temp_cleanup_failure_count": 0,
        }

    def fake_full_compile(output_records, target=2, compile_worker_count=2):
        return {
            "queued_after_syntax_pass_count": target,
            "full_compile_invocation_count": target,
            "full_compile_success_count": target,
            "runtime_success_count": target,
            "stdout_correct_count": target,
            "compiler_verified_correctness_rate": 1.0,
            "wrong_stdout_count": 0,
            "timeout_count": 0,
            "watchdog_timeout_count": 0,
            "permission_error_count": 0,
            "cleanup_failure_count": 0,
            "boundary_compiler_misroute_count": 0,
            "future_domain_compiled_count": 0,
            "recursion_production_compiled_count": 0,
            "pointer_compiled_count": 0,
            "io_compiled_count": 0,
            "batch_compile_validation_completed": True,
        }

    monkeypatch.setattr(scaleup, "run_msvc_frontend_syntax_filter", fake_frontend)
    monkeypatch.setattr(scaleup, "run_batch_compile_validation", fake_full_compile)
    return scaleup.run_v0_9_27_scaleup(tmp_path / "records", tmp_path / "dataset", target_samples=100, syntax_frontend_target=2, full_compile_target=2, compile_worker_count=2, **kwargs)


def test_endurance_requires_6h(tmp_path, monkeypatch):
    result = _run_quick(
        tmp_path,
        monkeypatch,
        wall_clock_min_hours=6.0,
        max_runtime_hours=0.00001,
        hard_stop_hours=0.00001,
        rolling_window_minutes=30,
        checkpoint_interval_minutes=1,
    )
    assert result["readiness"]["endurance_completed"] is False
    assert result["readiness"]["recommended_claim_level"] == "endurance_partial_needs_rerun"


def test_ready_for_release_false(tmp_path, monkeypatch):
    result = _run_quick(
        tmp_path,
        monkeypatch,
        wall_clock_min_hours=0.00001,
        max_runtime_hours=0.001,
        hard_stop_hours=0.001,
        rolling_window_minutes=1,
        checkpoint_interval_minutes=1,
    )
    assert result["readiness"]["ready_for_v1_0_release"] is False


def test_no_formal_turing_claim(tmp_path, monkeypatch):
    result = _run_quick(
        tmp_path,
        monkeypatch,
        wall_clock_min_hours=0.00001,
        max_runtime_hours=0.001,
        hard_stop_hours=0.001,
        rolling_window_minutes=1,
        checkpoint_interval_minutes=1,
    )
    assert result["readiness"]["formal_turing_completeness_proven"] is False


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*function_array*.py"))
    assert "import expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*function_array*.py"))
    assert "openai" not in text.lower()
    assert "requests." not in text.lower()


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*function_array*.py"))
    assert "keyword_gate" not in text
    assert "keyword rejection gate" not in text


def test_real_promotion_disabled(tmp_path, monkeypatch):
    result = _run_quick(
        tmp_path,
        monkeypatch,
        wall_clock_min_hours=0.00001,
        max_runtime_hours=0.001,
        hard_stop_hours=0.001,
        rolling_window_minutes=1,
        checkpoint_interval_minutes=1,
    )
    assert result["architecture"]["real_promotion_disabled"] is True
