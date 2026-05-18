import sys
import os
import shutil
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu.runtime import Runtime
from jianmu.ir import ProgramIR

HAS_COMPILER = bool(
    shutil.which("gcc") or shutil.which("clang") or
    shutil.which("gcc", path=os.environ.get("PATH", "") + os.pathsep + "/data/data/com.termux/files/usr/bin") or
    shutil.which("clang", path=os.environ.get("PATH", "") + os.pathsep + "/data/data/com.termux/files/usr/bin")
)
needs_compiler = pytest.mark.skipif(not HAS_COMPILER, reason="gcc/clang not found")

ROOT = os.path.join(os.path.dirname(__file__), "..")


@pytest.fixture
def rt(tmp_path):
    r = Runtime()
    r._cache._path = str(tmp_path / "trace_cache.json")
    return r


# ── 1. __pycache__ 和 .pyc 被 .gitignore 覆盖 ────────────────────────────────
def test_no_pycache_or_pyc_committed():
    # pytest imports modules and inevitably creates __pycache__ at runtime.
    # The correct check is that .gitignore excludes them, not that they are
    # absent from the filesystem during a test run.
    gitignore = os.path.join(ROOT, ".gitignore")
    assert os.path.exists(gitignore), ".gitignore missing"
    content = open(gitignore).read()
    assert "__pycache__/" in content, "__pycache__/ not in .gitignore"
    assert "*.pyc" in content, "*.pyc not in .gitignore"


# ── 2. .pytest_cache 被 .gitignore 覆盖 ──────────────────────────────────────
def test_no_pytest_cache_committed():
    gitignore = os.path.join(ROOT, ".gitignore")
    content = open(gitignore).read()
    assert ".pytest_cache/" in content, ".pytest_cache/ not in .gitignore"


# ── 3. 无 trace_cache.json ────────────────────────────────────────────────────
def test_no_trace_cache_json_committed():
    cache_file = os.path.join(ROOT, "data", "trace_cache.json")
    assert not os.path.exists(cache_file), "data/trace_cache.json exists — should not be committed"


# ── 4. 错误 expected_output 不写入 TraceCache ─────────────────────────────────
@needs_compiler
def test_wrong_expected_output_not_cached(rt):
    # Run with deliberately wrong expected_output
    r = rt.run("生成两个 int 相加并打印", expected_output="999\n")

    assert r.score_report.compile_success == 1
    assert r.score_report.run_success == 1
    assert r.score_report.expected_output_match == 0
    assert r.score_report.correctness_score < 1.0

    # Second run must also be cache miss (nothing was cached)
    r2 = rt.run("生成两个 int 相加并打印", expected_output="999\n")
    assert not r2.cache_hit
