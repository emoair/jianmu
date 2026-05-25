from __future__ import annotations

import json
from pathlib import Path
import subprocess

from jianmu.self_learning.darwinforge.arithmetic_compiler_audit_readiness import assess_compiler_audit_readiness
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, detect_msvc_and_path_compilers


def test_msvc_detection_uses_vswhere_when_cl_not_in_path(monkeypatch, tmp_path: Path) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_compiler_backend as backend

    vcvars = tmp_path / "vcvars64.bat"
    vcvars.write_text("@echo off\n", encoding="utf-8")

    monkeypatch.setattr(backend.shutil, "which", lambda name: None)
    monkeypatch.setattr(backend.Path, "exists", lambda self: str(self).endswith("vswhere.exe") or self == vcvars)

    def fake_run(cmd, capture_output=True, text=True, timeout=15, cwd=None, **kwargs):
        joined = " ".join(map(str, cmd))
        if "vswhere" in joined:
            return subprocess.CompletedProcess(cmd, 0, str(vcvars) + "\n", "")
        if "cl_bv_test.bat" in joined or "cl /Bv" in joined:
            return subprocess.CompletedProcess(cmd, 0, "Microsoft C/C++ Optimizing Compiler", "")
        return subprocess.CompletedProcess(cmd, 1, "", "unexpected")

    monkeypatch.setattr(backend.subprocess, "run", fake_run)
    report = detect_msvc_and_path_compilers()
    assert report["vswhere_found"] is True
    assert report["vcvars64_found"] is True
    assert report["cl_bv_test_passed"] is True


def test_msvc_detection_marks_cl_available_after_vcvars(monkeypatch, tmp_path: Path) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_compiler_backend as backend

    vcvars = tmp_path / "vcvars64.bat"
    vcvars.write_text("@echo off\n", encoding="utf-8")
    monkeypatch.setattr(backend.shutil, "which", lambda name: None)
    monkeypatch.setattr(backend.Path, "exists", lambda self: str(self).endswith("vswhere.exe") or self == vcvars)

    def fake_run(cmd, capture_output=True, text=True, timeout=15, cwd=None, **kwargs):
        joined = " ".join(map(str, cmd))
        if "vswhere" in joined:
            return subprocess.CompletedProcess(cmd, 0, str(vcvars) + "\n", "")
        if "cl_bv_test.bat" in joined or "cl /Bv" in joined:
            return subprocess.CompletedProcess(cmd, 0, "cl ok", "")
        return subprocess.CompletedProcess(cmd, 1, "", "unexpected")

    monkeypatch.setattr(backend.subprocess, "run", fake_run)
    monkeypatch.setattr(backend, "detect_supported_c_compiler", lambda: (None, ""))
    detected = detect_arithmetic_backend(prefer_msvc=True)
    assert detected.backend_type == "real_c_compiler"
    assert detected.compiler_name == "cl"
    assert detected.compiler_environment == "msvc_vcvars64"


def test_compiler_backend_does_not_mark_python_as_real_compiler(monkeypatch) -> None:
    import jianmu.self_learning.darwinforge.arithmetic_compiler_backend as backend

    monkeypatch.setattr(backend, "detect_msvc_and_path_compilers", lambda: {
        "path_cl_found": False,
        "path_gcc_found": False,
        "path_clang_found": False,
        "vswhere_found": False,
        "vcvars64_found": False,
        "vcvars64_path": "",
        "cl_bv_test_passed": False,
        "cl_version_text_tail": "",
        "detection_conclusion": "no_c_compiler_detected",
    })
    monkeypatch.setattr(backend, "detect_supported_c_compiler", lambda: (None, ""))
    detected = detect_arithmetic_backend(prefer_python_subprocess=True, prefer_msvc=True)
    assert detected.backend_type == "python_subprocess_executor"
    assert not detected.compiler_available


def test_cl_backend_requires_real_invocation_count() -> None:
    readiness = assess_compiler_audit_readiness({
        "audit_completed": True,
        "backend_type": "real_c_compiler",
        "real_compiler_invocation_count": 0,
        "compiler_spot_sample_count": 10,
        "compiler_verified_correct_rate": 1.0,
        "boundary_compiler_misroute_count": 0,
        "forbidden_field_access_count": 0,
        "backend_claim_safe": True,
    })
    assert readiness["recommended_claim_level"] == "failed"
    assert "real_compiler_not_invoked" in readiness["blocking_issues"]


def test_compiler_audit_readiness_requires_real_compiler() -> None:
    readiness = assess_compiler_audit_readiness({
        "audit_completed": True,
        "backend_type": "python_subprocess_executor",
        "real_compiler_invocation_count": 0,
        "compiler_verified_correct_rate": None,
        "boundary_compiler_misroute_count": 0,
        "forbidden_field_access_count": 0,
        "backend_claim_safe": True,
    })
    assert readiness["recommended_claim_level"] == "execution_backed_but_not_compiler"
    assert "real_c_compiler_unavailable" in readiness["blocking_issues"]


def test_no_expression_oracle_import() -> None:
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in [
        "jianmu/self_learning/darwinforge/arithmetic_compiler_backend.py",
        "jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py",
    ])
    assert "expression_oracle" not in source


def test_no_external_api_calls() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_compiler_backend.py").read_text(encoding="utf-8")
    assert "openai" not in source.lower()
    assert "requests." not in source


def test_no_hardcoded_keyword_gate() -> None:
    source = Path("jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py").read_text(encoding="utf-8")
    assert "keyword" not in source.lower()


def test_real_promotion_disabled() -> None:
    source = json.dumps({
        "backend": Path("jianmu/self_learning/darwinforge/arithmetic_compiler_backend.py").read_text(encoding="utf-8"),
        "audit": Path("jianmu/self_learning/darwinforge/arithmetic_compiler_spot_audit.py").read_text(encoding="utf-8"),
    })
    assert "real_promotion" not in source
