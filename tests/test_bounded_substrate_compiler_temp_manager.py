from __future__ import annotations

import inspect
from pathlib import Path

from jianmu.self_learning.darwinforge import bounded_substrate_compiler_temp_manager as temp_manager


def test_temp_manager_uses_unique_per_sample_dirs(tmp_path: Path) -> None:
    first = temp_manager.make_sample_temp_dir(tmp_path, "run", 1, "abc")
    second = temp_manager.make_sample_temp_dir(tmp_path, "run", 1, "abc")
    assert first != second
    assert first.exists()
    assert second.exists()


def test_temp_manager_cleanup_permission_error_is_separate(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = temp_manager.cleanup_temp_dir(missing)
    assert result["cleanup_success"] is True


def test_temp_manager_uses_subprocess_list_args() -> None:
    source = inspect.getsource(temp_manager.validate_sample_with_temp_manager)
    assert "shell=True" not in source
    assert "subprocess.run(cmd" in source
