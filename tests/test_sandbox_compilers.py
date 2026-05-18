import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from jianmu import sandbox
from jianmu.sandbox import (
    SUPPORTED_COMPILERS,
    Sandbox,
    detect_supported_c_compiler,
    has_supported_c_compiler,
)


MINIMAL_C = '#include <stdio.h>\nint main(void) { printf("%d\\n", 3); return 0; }\n'


def test_detects_any_supported_c_compiler(monkeypatch):
    for available in SUPPORTED_COMPILERS:
        def fake_which(name, path=None, available=available):
            return f"/fake/{name}" if name == available else None

        monkeypatch.setattr(sandbox.shutil, "which", fake_which)
        compiler, compiler_name = detect_supported_c_compiler()

        assert compiler == f"/fake/{available}"
        assert compiler_name == available
        assert has_supported_c_compiler()


def test_sandbox_can_compile_with_detected_compiler():
    if not has_supported_c_compiler():
        pytest.skip("gcc/clang/cl not found")

    result = Sandbox().run(MINIMAL_C)

    assert result.compiler in SUPPORTED_COMPILERS
    assert result.compile_success, result.stderr or result.stdout
    assert result.run_success, result.stderr or result.stdout
    assert result.stdout == "3\n"


def test_cl_command_shape_if_cl_selected():
    compiler, compiler_name = detect_supported_c_compiler("cl")
    if not compiler or compiler_name != "cl":
        pytest.skip("cl not found")

    result = Sandbox(compiler="cl").run(MINIMAL_C)

    assert result.compiler == "cl"
    assert result.compile_success, result.stderr or result.stdout
    assert result.run_success, result.stderr or result.stdout
    assert "/nologo" in result.command
    assert "/TC" in result.command
    assert "/Fe:" in result.command
    assert "/Fo:" in result.command
