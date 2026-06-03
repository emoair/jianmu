from pathlib import Path

from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy import write_failure_taxonomy


def test_batch_compile_failure_taxonomy_reads_v27_failures(tmp_path):
    result = write_failure_taxonomy("records/v0_9_27", tmp_path)
    assert result["taxonomy_completed"] is True
    assert result["original_full_compile_invocation_count"] == 20000
    assert result["unique_failed_sample_count"] == 5


def test_wrong_stdout_timeout_overlap_reported(tmp_path):
    result = write_failure_taxonomy("records/v0_9_27", tmp_path)
    assert result["overlap_count"] == 5
    assert set(result["wrong_stdout_sample_ids"]) == set(result["timeout_sample_ids"])
    assert Path(tmp_path / "batch_compile_failure_taxonomy.md").exists()
