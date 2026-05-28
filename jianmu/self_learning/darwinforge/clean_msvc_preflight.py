from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_msvc_and_path_compilers


def run_clean_msvc_preflight(output_records: str | Path, working_directory: str | Path | None = None) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    wd = Path(working_directory or Path.cwd())
    report = detect_msvc_and_path_compilers()
    stale = _stale_process_summary()
    tmp_ok = _check_tmp_writable()
    warnings: List[str] = []
    blockers: List[str] = []
    if stale["stale_cl_process_count"] or stale["stale_link_process_count"]:
        warnings.append("stale cl/link process detected; validation may be unstable")
    if stale["stale_python_process_count"] > 1:
        warnings.append("additional python processes detected; not killed by preflight")
    if "OneDrive" in str(wd):
        warnings.append("working directory is under OneDrive; compiler tmp uses system temp")
    if not report.get("cl_bv_test_passed"):
        blockers.append("cl /Bv did not pass through PATH/vswhere/vcvars64")
    if not tmp_ok:
        blockers.append("compiler temp directory is not writable")
    result = {
        "os_name": os.name,
        "current_process_id": os.getpid(),
        "python_executable": sys.executable,
        "working_directory": str(wd),
        "vswhere_found": report.get("vswhere_found", False),
        "vcvars64_found": report.get("vcvars64_found", False),
        "vcvars64_path": report.get("vcvars64_path", ""),
        "cl_bv_test_passed": report.get("cl_bv_test_passed", False),
        "cl_version_tail": report.get("cl_version_text_tail", ""),
        "path_cl_found": report.get("path_cl_found", False),
        "path_link_found": _which_exists("link"),
        **stale,
        **_security_process_summary(stale.get("stale_process_summary", [])),
        "one_drive_path_detected": "OneDrive" in str(wd),
        "compiler_tmp_dir_writable": tmp_ok,
        "preflight_passed": not blockers,
        "preflight_warnings": warnings,
        "preflight_blocking_issues": blockers,
    }
    _write_json(out / "clean_msvc_preflight.json", result)
    (out / "clean_msvc_preflight.md").write_text(_render_preflight_md(result), encoding="utf-8")
    return result


def _stale_process_summary() -> Dict[str, Any]:
    summary = {
        "stale_cl_process_count": 0,
        "stale_link_process_count": 0,
        "stale_python_process_count": 0,
        "stale_process_summary": [],
    }
    try:
        import subprocess

        proc = subprocess.run(["tasklist.exe", "/FO", "CSV"], capture_output=True, text=True, timeout=10, errors="replace")
    except Exception as exc:
        summary["stale_process_summary"].append({"error": type(exc).__name__})
        return summary
    current = str(os.getpid())
    for line in proc.stdout.splitlines()[1:]:
        parts = [part.strip().strip('"') for part in line.split('","')]
        if len(parts) < 2:
            continue
        name, pid = parts[0].lower(), parts[1]
        if name in {"cl.exe", "link.exe", "python.exe", "360tray.exe", "360sd.exe", "360safe.exe", "msmpeng.exe", "securityhealthservice.exe"} and pid != current:
            summary["stale_process_summary"].append({"process_name": name, "pid": pid})
            if name == "cl.exe":
                summary["stale_cl_process_count"] += 1
            elif name == "link.exe":
                summary["stale_link_process_count"] += 1
            elif name == "python.exe":
                summary["stale_python_process_count"] += 1
    return summary


def _security_process_summary(processes: List[Dict[str, Any]]) -> Dict[str, Any]:
    names = {str(row.get("process_name", "")).lower() for row in processes}
    known_360 = any(name.startswith("360") for name in names)
    defender = any(name in {"msmpeng.exe", "securityhealthservice.exe"} for name in names)
    return {
        "antivirus_process_suspected": known_360 or defender,
        "defender_or_security_lock_suspected": defender,
        "known_360_process_detected": known_360,
    }


def _check_tmp_writable() -> bool:
    root = Path(tempfile.gettempdir()) / "jianmu_v0_9_7_3_preflight"
    try:
        root.mkdir(parents=True, exist_ok=True)
        test = root / "write_test.txt"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
        root.rmdir()
        return True
    except OSError:
        return False


def _which_exists(name: str) -> bool:
    import shutil

    return shutil.which(name) is not None


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_preflight_md(result: Dict[str, Any]) -> str:
    lines = ["# Clean MSVC Preflight", ""]
    for key in ["preflight_passed", "vswhere_found", "vcvars64_found", "cl_bv_test_passed", "stale_cl_process_count", "stale_link_process_count", "stale_python_process_count"]:
        lines.append(f"- {key}: {result.get(key)}")
    return "\n".join(lines) + "\n"
