from jianmu.self_learning.darwinforge.turing_frontier_true_endurance import run_true_endurance_scaleup


def test_readiness_requires_endurance_and_frontier_thresholds(tmp_path):
    result = run_true_endurance_scaleup(
        "records/v0_9_26",
        "datasets/v0_9_26_turing_frontier",
        tmp_path / "records",
        tmp_path / "dataset",
        target_samples=1000,
        compiler_target=4,
        compile_worker_count=2,
        wall_clock_min_hours=12.0,
        max_runtime_hours=0.00001,
        hard_stop_hours=0.00001,
        rolling_window_minutes=30,
        checkpoint_interval_minutes=1,
    )
    readiness = result["readiness"]
    assert readiness["true_endurance_completed"] is False
    assert readiness["ready_for_turing_substrate_freeze_candidate"] is False
    assert readiness["recommended_claim_level"] == "endurance_partial_needs_rerun"


def test_ready_for_release_false(tmp_path):
    result = run_true_endurance_scaleup(
        "records/v0_9_26",
        "datasets/v0_9_26_turing_frontier",
        tmp_path / "records",
        tmp_path / "dataset",
        target_samples=1000,
        compiler_target=4,
        compile_worker_count=2,
        wall_clock_min_hours=0.00001,
        max_runtime_hours=0.001,
        hard_stop_hours=0.001,
        rolling_window_minutes=1,
        checkpoint_interval_minutes=1,
    )
    assert result["readiness"]["ready_for_v1_0_release"] is False


def test_no_formal_turing_claim(tmp_path):
    result = run_true_endurance_scaleup(
        "records/v0_9_26",
        "datasets/v0_9_26_turing_frontier",
        tmp_path / "records",
        tmp_path / "dataset",
        target_samples=1000,
        compiler_target=4,
        compile_worker_count=2,
        wall_clock_min_hours=0.00001,
        max_runtime_hours=0.001,
        hard_stop_hours=0.001,
        rolling_window_minutes=1,
        checkpoint_interval_minutes=1,
    )
    assert "formal Turing completeness proof" in result["readiness"]["required_next_run"] or result["readiness"]["ready_for_v1_0_release"] is False


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*turing_frontier*.py"))
    assert "import expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*turing_frontier*.py"))
    assert "openai" not in text.lower()
    assert "requests." not in text.lower()


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*turing_frontier*.py"))
    assert "keyword_gate" not in text
    assert "keyword rejection gate" not in text


def test_real_promotion_disabled(tmp_path):
    result = run_true_endurance_scaleup(
        "records/v0_9_26",
        "datasets/v0_9_26_turing_frontier",
        tmp_path / "records",
        tmp_path / "dataset",
        target_samples=1000,
        compiler_target=4,
        compile_worker_count=2,
        wall_clock_min_hours=0.00001,
        max_runtime_hours=0.001,
        hard_stop_hours=0.001,
        rolling_window_minutes=1,
        checkpoint_interval_minutes=1,
    )
    assert result["architecture"]["real_promotion_disabled"] is True
