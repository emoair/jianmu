import os

from jianmu.self_learning.darwinforge.process_tree_memory_sampler import sample_process_tree


def test_process_tree_memory_sampler_tracks_children() -> None:
    result = sample_process_tree(os.getpid())
    assert result["parent_pid"] == os.getpid()
    assert "process_tree_rss_mb" in result
