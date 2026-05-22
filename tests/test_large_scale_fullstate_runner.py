from jianmu.self_learning.darwinforge.large_scale_fullstate_runner import run_large_scale_fullstate_reproduction


def test_large_scale_runner_quick_mode(tmp_path):
    result = run_large_scale_fullstate_reproduction(
        dataset_dir="datasets/v0_8_5_boundary_aware",
        source_records="records",
        output_records=tmp_path,
        modes=["quick"],
        seeds=[42],
        max_runtime_hours=1,
    )
    assert result["summary"]["modes_completed"] == ["quick"]
    assert (tmp_path / "mainline_conclusion.json").exists()


def test_large_scale_runner_marks_partial_correctly(tmp_path):
    result = run_large_scale_fullstate_reproduction(
        dataset_dir="datasets/v0_8_5_boundary_aware",
        source_records="records",
        output_records=tmp_path,
        modes=["quick", "longrun"],
        seeds=[42],
        max_runtime_hours=1,
    )
    partial = result["summary"]["modes_partial_skipped"]
    assert any(row["mode"] == "longrun" and row["status"] == "partial" for row in partial)
