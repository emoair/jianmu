import sys

from jianmu.self_learning.darwinforge.subprocess_lifecycle_guard import run_guarded_subprocess


def test_subprocess_lifecycle_guard_waits_and_kills_on_timeout():
    result = run_guarded_subprocess([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.2)
    assert result.timed_out is True
    assert result.terminated is True
    assert result.cleanup_status in {"terminated_after_timeout", "killed_after_timeout", "clean"}
