from jianmu.self_learning.darwinforge.real_longrun_runner import run_cross_process_child, run_real_longrun_with_counters


def test_real_longrun_runner_real_mini(tmp_path):
    result = run_real_longrun_with_counters(
        dataset_dir="datasets/v0_8_5_boundary_aware",
        output_records=tmp_path / "records",
        modes=["real-mini"],
        seeds=[42],
    )
    summary = result["summary"]
    assert summary["largest_completed_real_mode"] == "real-mini"
    assert summary["actual_train_iterated_count"] == 500
    assert summary["actual_eval_iterated_count"] == 200
    assert summary["actual_external_ood_iterated_count"] == 200
    assert (tmp_path / "records" / "workload_trace.jsonl").exists()


def test_real_longrun_runner_marks_partial(tmp_path):
    result = run_real_longrun_with_counters(
        dataset_dir="datasets/v0_8_5_boundary_aware",
        output_records=tmp_path / "records",
        modes=["longrun-real"],
        seeds=[42],
    )
    assert result["summary"]["modes_partial_skipped"][0]["status"] == "partial"


def test_cross_process_real_trace_requires_child_eval(tmp_path):
    trace = run_cross_process_child(tmp_path, "real-mini", 3)
    assert trace["cross_process_real_execution_verified"] is True
    assert trace["child_eval_sample_count"] == 3


def test_mainline_conclusion_ledger_exists(tmp_path):
    run_real_longrun_with_counters(
        dataset_dir="datasets/v0_8_5_boundary_aware",
        output_records=tmp_path / "records",
        modes=["real-mini"],
        seeds=[42],
    )
    assert (tmp_path / "records" / "mainline_conclusion.md").exists()
