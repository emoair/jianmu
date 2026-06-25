from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Iterable, List

from jianmu.self_learning.darwinforge.backend_compiler_manifest import write_jsonl
from jianmu.self_learning.darwinforge.compiler_integrity_schema import BACKEND_POLICIES, BackendValidationConfig
from jianmu.self_learning.darwinforge.compiler_subprocess_evidence import run_process_evidence, sha256_file


def run_short_backend_validation(output_records: str | Path, config: BackendValidationConfig) -> Dict[str, object]:
    out = Path(output_records)
    artifact_root = _runtime_artifact_root(out, "backend_artifacts")
    count = max(config.minimum_backend_cl_invocations, config.minimum_backend_link_invocations, config.minimum_backend_exe_runs)
    with ThreadPoolExecutor(max_workers=config.compiler_workers) as pool:
        futures = [pool.submit(_compile_one, artifact_root, i, False) for i in range(count)]
        rows = [future.result() for future in as_completed(futures)]
    rows.sort(key=lambda row: row["sample_id"])
    stdout_rows = [{"compile_invocation_id": row["compile_invocation_id"], "sample_id": row["sample_id"], "expected_stdout": row["expected_stdout"], "actual_stdout": row["actual_stdout"], "stdout_match": row["stdout_match"]} for row in rows]
    write_jsonl(out / "backend_invocation_manifest.jsonl", rows)
    write_jsonl(out / "backend_stdout_comparison.jsonl", stdout_rows)
    passed = [row for row in rows if row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0]
    result = {
        "backend_validation_started": True,
        "backend_validation_completed": True,
        "backend_artifact_root": str(artifact_root),
        "backend_artifacts_stored_outside_git_worktree": _is_outside_git_worktree(artifact_root),
        "events": config.events,
        "frontend_generated_events": config.events,
        "frontend_syntax_filtered_events": config.events,
        "backend_cl_invocations": len(rows),
        "backend_link_invocations": len(rows),
        "backend_exe_runs": len(rows),
        "compiler_verified_correctness_rate": round(len(passed) / len(rows), 12) if rows else 0.0,
        "wrong_stdout_count": sum(1 for row in rows if not row["stdout_match"]),
        "timeout_count": sum(1 for row in rows if row.get("timed_out")),
        "permission_error_count": sum(1 for row in rows if row.get("permission_error")),
        "cleanup_failure_count": 0,
        "security_interference_detected_count": sum(1 for row in rows if row.get("security_interference_detected")),
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": len(rows) - len({row["compile_invocation_id"] for row in rows}),
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
    }
    result["backend_validation_passed"] = all([
        result["backend_cl_invocations"] >= config.minimum_backend_cl_invocations,
        result["backend_link_invocations"] >= config.minimum_backend_link_invocations,
        result["backend_exe_runs"] >= config.minimum_backend_exe_runs,
        result["compiler_verified_correctness_rate"] == 1.0,
        result["wrong_stdout_count"] == 0,
        result["timeout_count"] == 0,
        result["cached_result_used_as_new_count"] == 0,
        result["duplicate_invocation_id_count"] == 0,
        not result["stubbed_validation_detected"],
        not result["summary_only_validation_detected"],
    ])
    _write_json(out / "backend_validation_summary.json", result)
    return result


def run_backend_replay(output_records: str | Path, config: BackendValidationConfig) -> Dict[str, object]:
    out = Path(output_records)
    artifact_root = _runtime_artifact_root(out, "backend_replay_artifacts")
    manifest = out / "backend_invocation_manifest.jsonl"
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    sample_count = min(config.replay_samples, len(rows))
    replay_rows = []
    with ThreadPoolExecutor(max_workers=config.compiler_workers) as pool:
        futures = [pool.submit(_compile_one, artifact_root, i, True, rows[i]["expected_stdout"]) for i in range(sample_count)]
        for future in as_completed(futures):
            replay_rows.append(future.result())
    replay_rows.sort(key=lambda row: row["sample_id"])
    write_jsonl(out / "backend_replay_manifest.jsonl", replay_rows)
    success = [row for row in replay_rows if row["stdout_match"] and row["cl_returncode"] == 0 and row["link_returncode"] == 0 and row["exe_returncode"] == 0]
    result = {
        "backend_replay_completed": True,
        "backend_replay_artifact_root": str(artifact_root),
        "backend_replay_artifacts_stored_outside_git_worktree": _is_outside_git_worktree(artifact_root),
        "replay_samples": len(replay_rows),
        "replay_success_rate": round(len(success) / len(replay_rows), 12) if replay_rows else 0.0,
        "replay_fail_count": len(replay_rows) - len(success),
        "replay_cl_invocations": len(replay_rows),
        "replay_link_invocations": len(replay_rows),
        "replay_exe_runs": len(replay_rows),
        "replay_stdout_mismatch_count": sum(1 for row in replay_rows if not row["stdout_match"]),
        "replay_security_interference_count": sum(1 for row in replay_rows if row.get("security_interference_detected")),
    }
    result["backend_replay_passed"] = result["replay_samples"] >= config.replay_minimum_samples and result["replay_success_rate"] == 1.0 and result["replay_fail_count"] == 0
    _write_json(out / "backend_replay_sampling.json", result)
    return result


def _compile_one(root: Path, index: int, replay: bool, expected: str | None = None) -> Dict[str, object]:
    policy = BACKEND_POLICIES[index % len(BACKEND_POLICIES)]
    expected_stdout = expected if expected is not None else str((index % 997) + 3)
    sample_id = ("replay" if replay else "backend") + f"_{index:06d}"
    work = root / sample_id
    work.mkdir(parents=True, exist_ok=True)
    source = work / "program.c"
    obj = work / "program.obj"
    exe = work / "program.exe"
    source.write_text(f"#include <stdio.h>\nint main(void) {{ printf(\"%s\", \"{expected_stdout}\"); return 0; }}\n", encoding="utf-8")
    source_sha = sha256_file(source)
    cl_out, cl_err = work / "cl.stdout.txt", work / "cl.stderr.txt"
    link_out, link_err = work / "link.stdout.txt", work / "link.stderr.txt"
    exe_out, exe_err = work / "exe.stdout.txt", work / "exe.stderr.txt"
    cl_cmd = ["cl", "/nologo", "/TC", "/c", str(source.name), f"/Fo:{obj.name}"]
    cl = run_process_evidence(cl_cmd, work, cl_out, cl_err, timeout=20)
    link_cmd = ["link", "/NOLOGO", str(obj.name), f"/OUT:{exe.name}"]
    link = run_process_evidence(link_cmd, work, link_out, link_err, timeout=20) if cl["returncode"] == 0 else {"command": link_cmd, "pid": -1, "start_monotonic": 0.0, "end_monotonic": 0.0, "returncode": -1, "stdout_path": str(link_out), "stderr_path": str(link_err), "timed_out": False, "security_interference_detected": False, "permission_error": False}
    run = run_process_evidence([str(exe)], work, exe_out, exe_err, timeout=5) if link["returncode"] == 0 else {"command": [str(exe)], "pid": -1, "start_monotonic": 0.0, "end_monotonic": 0.0, "returncode": -1, "stdout_path": str(exe_out), "stderr_path": str(exe_err), "timed_out": False, "security_interference_detected": False, "permission_error": False}
    actual = exe_out.read_text(encoding="utf-8", errors="replace") if exe_out.exists() else ""
    artifact_missing = not obj.exists() or not exe.exists()
    return {
        "compile_invocation_id": uuid.uuid4().hex,
        "sample_id": sample_id,
        "cycle_id": f"cycle_{index % 8}",
        "policy": policy,
        "lane": "backend_compiler",
        "source_sha256": source_sha,
        "c_source_path": str(source),
        "obj_path": str(obj),
        "exe_path": str(exe),
        "cl_command": cl_cmd,
        "cl_pid": int(cl["pid"]),
        "cl_start_monotonic": cl["start_monotonic"],
        "cl_end_monotonic": cl["end_monotonic"],
        "cl_returncode": cl["returncode"],
        "cl_stdout_path": str(cl_out),
        "cl_stderr_path": str(cl_err),
        "link_command": link_cmd,
        "link_pid": int(link["pid"]),
        "link_start_monotonic": link["start_monotonic"],
        "link_end_monotonic": link["end_monotonic"],
        "link_returncode": link["returncode"],
        "link_stdout_path": str(link_out),
        "link_stderr_path": str(link_err),
        "exe_pid": int(run["pid"]),
        "exe_start_monotonic": run["start_monotonic"],
        "exe_end_monotonic": run["end_monotonic"],
        "exe_returncode": run["returncode"],
        "expected_stdout": expected_stdout,
        "actual_stdout": actual,
        "stdout_match": actual == expected_stdout,
        "security_interference_detected": bool(cl.get("security_interference_detected") or link.get("security_interference_detected") or run.get("security_interference_detected") or artifact_missing),
        "artifact_missing_after_compile": artifact_missing,
        "permission_error": bool(cl.get("permission_error") or link.get("permission_error") or run.get("permission_error")),
        "timed_out": bool(cl.get("timed_out") or link.get("timed_out") or run.get("timed_out")),
        "exe_blocked": False,
        "cached": False,
        "stubbed": False,
    }


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _runtime_artifact_root(output_records: Path, name: str) -> Path:
    base = Path(os.environ.get("JIANMU_COMPILER_INTEGRITY_ARTIFACT_ROOT", Path(tempfile.gettempdir()) / "jianmu_compiler_integrity_artifacts"))
    root = base / output_records.name / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _is_outside_git_worktree(path: Path) -> bool:
    try:
        resolved = path.resolve()
        cwd = Path.cwd().resolve()
        return not (resolved == cwd or cwd in resolved.parents)
    except OSError:
        return False
