# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
import tempfile
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_COMPILERS = ("gcc", "clang", "cl")


@dataclass
class SandboxResult:
    compiler: str
    compile_success: bool
    run_success: bool
    stdout: str
    stderr: str
    returncode: int
    error_type: str
    command: str


def _compiler_search_path() -> str:
    return os.environ.get("PATH", "") + os.pathsep + "/data/data/com.termux/files/usr/bin"


def _compiler_name(compiler: str) -> str:
    return Path(compiler).stem.lower()


def detect_supported_c_compiler(compiler: str = None):
    """Return (compiler_path, compiler_name) for gcc, clang, or MSVC cl."""
    search_path = _compiler_search_path()

    if compiler:
        if os.path.isabs(compiler) and os.path.exists(compiler):
            found = compiler
        else:
            found = shutil.which(compiler, path=search_path)
        if not found:
            return None, ""
        name = _compiler_name(found)
        if name not in SUPPORTED_COMPILERS:
            return None, ""
        return found, name

    for name in SUPPORTED_COMPILERS:
        found = shutil.which(name, path=search_path)
        if found:
            return found, name
    return None, ""


def has_supported_c_compiler() -> bool:
    compiler, _ = detect_supported_c_compiler()
    return bool(compiler)


def build_compile_command(compiler: str, compiler_name: str, src: Path, exe: Path):
    if compiler_name == "cl":
        obj = exe.with_suffix(".obj")
        return [
            compiler,
            "/nologo",
            "/TC",
            src.name,
            f"/Fe:{exe.name}",
            f"/Fo:{obj.name}",
        ]
    return [compiler, str(src), "-o", str(exe)]


def _format_command(command) -> str:
    return subprocess.list2cmdline([str(part) for part in command])


class Sandbox:
    def __init__(self, compiler: str = None):
        self.compiler = compiler

    def run(self, source_code: str, timeout: int = 15, compiler: str = None) -> SandboxResult:
        compiler, compiler_name = detect_supported_c_compiler(compiler or self.compiler)

        if not compiler:
            return SandboxResult(
                compiler="", compile_success=False, run_success=False,
                stdout="", stderr="", returncode=-1,
                error_type="no_compiler", command=""
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            src = tmp_path / "prog.c"
            exe = tmp_path / ("prog.exe" if os.name == "nt" else "prog")
            with open(src, "w", encoding="utf-8") as f:
                f.write(source_code)

            compile_cmd = build_compile_command(compiler, compiler_name, src, exe)
            compile_cmd_text = _format_command(compile_cmd)
            try:
                cp = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpdir,
                )
            except subprocess.TimeoutExpired as e:
                return SandboxResult(
                    compiler=compiler_name, compile_success=False, run_success=False,
                    stdout=e.stdout or "", stderr=e.stderr or "", returncode=-1,
                    error_type="compile_timeout", command=compile_cmd_text
                )
            if cp.returncode != 0:
                return SandboxResult(
                    compiler=compiler_name, compile_success=False, run_success=False,
                    stdout=cp.stdout, stderr=cp.stderr, returncode=cp.returncode,
                    error_type="compile_error", command=compile_cmd_text
                )

            run_cmd = str(exe)
            try:
                rp = subprocess.run(
                    [str(exe)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpdir,
                )
                return SandboxResult(
                    compiler=compiler_name, compile_success=True,
                    run_success=(rp.returncode == 0),
                    stdout=rp.stdout, stderr=cp.stderr + rp.stderr, returncode=rp.returncode,
                    error_type="" if rp.returncode == 0 else "runtime_error",
                    command=compile_cmd_text
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    compiler=compiler_name, compile_success=True, run_success=False,
                    stdout="", stderr=cp.stderr, returncode=-1,
                    error_type="timeout", command=run_cmd
                )
