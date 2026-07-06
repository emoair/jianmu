from jianmu.self_learning.darwinforge.system_commit_cache_pool_sampler import sample_commit_cache_pool


def test_system_commit_cache_pool_sampler() -> None:
    result = sample_commit_cache_pool()
    assert result["commit_limit_mb"] >= 0
    assert "paged_pool_mb" in result
