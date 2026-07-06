from jianmu.self_learning.darwinforge.security_onedrive_git_classifier import classify_process
from jianmu.self_learning.darwinforge.top_process_memory_snapshot import collect_top_process_memory


def test_top_process_memory_snapshot_classifies_git() -> None:
    assert classify_process("git.exe", "git status --porcelain") in {"git", "ide"}
    result = collect_top_process_memory(5)
    assert "top_processes" in result
