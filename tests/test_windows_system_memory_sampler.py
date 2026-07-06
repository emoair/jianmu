from jianmu.self_learning.darwinforge.windows_system_memory_sampler import sample_windows_system_memory, write_system_memory_sampler_contract


def test_windows_system_memory_sampler_records_commit(tmp_path) -> None:
    sample = sample_windows_system_memory()
    assert sample["commit_limit_mb"] >= 0
    result = write_system_memory_sampler_contract(tmp_path, sample)
    assert result["physical_memory_recorded"] is True
    assert result["commit_recorded"] is True
