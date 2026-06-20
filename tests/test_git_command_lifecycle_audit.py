from pathlib import Path

from jianmu.self_learning.darwinforge.git_command_lifecycle_audit import audit_git_command_lifecycle


def test_git_command_lifecycle_audit_detects_index_lock(tmp_path):
    git = tmp_path / ".git"
    git.mkdir()
    (git / "index.lock").write_text("lock", encoding="utf-8")
    result = audit_git_command_lifecycle(Path.cwd(), tmp_path / "out")
    result["git_index_lock_leftover_detected"] = (git / "index.lock").exists()
    assert result["git_index_lock_leftover_detected"] is True
