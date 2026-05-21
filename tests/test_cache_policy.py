from pathlib import Path

from jianmu.self_learning.runtime.cache_policy import RuntimeCachePolicy, resolve_runtime_cache


def test_cache_policy_allows_project_local_cache(tmp_path):
    summary = resolve_runtime_cache(tmp_path, policy=RuntimeCachePolicy(prefer_project_local_cache=True, user_allows_project_local_cache=True))
    assert ".jianmu_runtime_cache" in summary["runtime_cache_dir"]
    assert summary["user_allows_project_local_cache"] is True
    assert summary["cache_write_test_passed"]


def test_cache_policy_does_not_force_avoid_onedrive():
    project = Path("C:/Users/Air/OneDrive/文档/jianmu-mvp")
    summary = resolve_runtime_cache(project, policy=RuntimeCachePolicy(prefer_project_local_cache=True, user_allows_project_local_cache=True))
    assert "OneDrive" in summary["runtime_cache_dir"]
    assert summary["project_inside_onedrive"] is True
    assert summary["onedrive_sync_state"] == "not_measured"

