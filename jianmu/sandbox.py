import subprocess
import tempfile
import os
import shutil
from dataclasses import dataclass, field


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


class Sandbox:
    def run(self, source_code: str, timeout: int = 5) -> SandboxResult:
        extra = os.environ.get("PATH", "") + os.pathsep + "/data/data/com.termux/files/usr/bin"
        compiler = shutil.which("gcc", path=extra) or shutil.which("clang", path=extra)
        compiler_name = os.path.basename(compiler) if compiler else ""

        if not compiler:
            return SandboxResult(
                compiler="", compile_success=False, run_success=False,
                stdout="", stderr="", returncode=-1,
                error_type="no_compiler", command=""
            )

        tmpdir = tempfile.mkdtemp()
        try:
            src = os.path.join(tmpdir, "prog.c")
            exe = os.path.join(tmpdir, "prog")
            with open(src, "w") as f:
                f.write(source_code)

            compile_cmd = f"{compiler} {src} -o {exe}"
            cp = subprocess.run(
                [compiler, src, "-o", exe],
                capture_output=True, text=True
            )
            if cp.returncode != 0:
                return SandboxResult(
                    compiler=compiler_name, compile_success=False, run_success=False,
                    stdout="", stderr=cp.stderr, returncode=cp.returncode,
                    error_type="compile_error", command=compile_cmd
                )

            run_cmd = exe
            try:
                rp = subprocess.run(
                    [exe], capture_output=True, text=True, timeout=timeout
                )
                return SandboxResult(
                    compiler=compiler_name, compile_success=True,
                    run_success=(rp.returncode == 0),
                    stdout=rp.stdout, stderr=rp.stderr, returncode=rp.returncode,
                    error_type="" if rp.returncode == 0 else "runtime_error",
                    command=run_cmd
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    compiler=compiler_name, compile_success=True, run_success=False,
                    stdout="", stderr="", returncode=-1,
                    error_type="timeout", command=run_cmd
                )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
