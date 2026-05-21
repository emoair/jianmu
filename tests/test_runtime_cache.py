from pathlib import Path

from jianmu.self_learning.runtime.runtime_cache import init_runtime_cache


def test_runtime_cache_avoids_onedrive_by_default(tmp_path):
    project = Path("C:/Users/Air/OneDrive/文档/jianmu-mvp")
    summary = init_runtime_cache(project)
    assert summary["cache_write_test_passed"]
    assert "OneDrive" not in summary["runtime_cache_dir"]
    assert summary["project_inside_onedrive"] is True

