from jianmu.self_learning.darwinforge.redqueen_lifecycle_readiness import build_redqueen_lifecycle_readiness


def _parts():
    return (
        {"process_lifecycle_audit_completed": True},
        {"subprocess_lifecycle_guard_passed": True},
        {"executor_shutdown_guard_passed": True},
        {"trace_writer_shutdown_guard_passed": True},
        {"git_lifecycle_audit_passed": True},
        {"post_run_idle_sentinel_passed": True, "lingering_python_child_count": 0, "lingering_git_process_count": 0, "lingering_compiler_process_count": 0, "active_worker_thread_count": 0, "open_manifest_handle_count": 0, "git_index_lock_leftover_detected": False},
        {"redqueen_short_replay_passed": True, "workers_requested": 16, "workers_used": 16, "compiler_workers_requested": 16, "compiler_workers_used": 16, "default_profile_unchanged": True, "real_promotion_enabled": False},
    )


def test_redqueen_lifecycle_readiness_requires_no_lingering_python(tmp_path):
    parts = list(_parts())
    parts[5] = {**parts[5], "lingering_python_child_count": 1}
    result = build_redqueen_lifecycle_readiness(tmp_path, *parts)
    assert result["recommended_claim_level"] == "lifecycle_blocked_by_lingering_python"


def test_redqueen_lifecycle_readiness_requires_no_lingering_git(tmp_path):
    parts = list(_parts())
    parts[5] = {**parts[5], "lingering_git_process_count": 1}
    result = build_redqueen_lifecycle_readiness(tmp_path, *parts)
    assert result["recommended_claim_level"] == "lifecycle_blocked_by_lingering_git"


def test_redqueen_lifecycle_readiness_keeps_production_false(tmp_path):
    result = build_redqueen_lifecycle_readiness(tmp_path, *_parts())
    assert result["redqueen_process_lifecycle_clean"] is True
    assert result["production_function_support_completed"] is False
    assert result["ready_for_official_release"] is False


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*lifecycle*.py"))
    assert "expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*lifecycle*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_real_promotion_disabled():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/redqueen_lifecycle_readiness.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": True' not in text
