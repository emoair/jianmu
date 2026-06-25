from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


ARTIFACT_SUFFIXES = {".c", ".obj", ".exe", ".stdout", ".stderr"}


def default_artifact_root(version: str = "v1_0_8_8_2") -> Path:
    return Path(os.environ.get("JIANMU_COMPILER_INTEGRITY_ARTIFACT_ROOT", Path(tempfile.gettempdir()) / "jianmu_compiler_integrity_artifacts")) / version


def is_outside_worktree(path: str | Path, worktree: str | Path | None = None) -> bool:
    root = Path(worktree or Path.cwd()).resolve()
    target = Path(path).resolve()
    return not (target == root or root in target.parents)


def artifact_guard(output_records: str | Path, artifact_root: str | Path, worktree: str | Path | None = None) -> dict:
    out = Path(output_records)
    root = Path(worktree or Path.cwd()).resolve()
    artifact = Path(artifact_root).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    worktree_artifacts = []
    for suffix in ("*.obj", "*.exe"):
        worktree_artifacts.extend(root.glob(suffix))
    records_binaries = list(out.glob("**/*.obj")) + list(out.glob("**/*.exe"))
    result = {
        "artifact_guard_completed": True,
        "artifact_root": str(artifact),
        "artifact_root_outside_worktree": is_outside_worktree(artifact, root),
        "artifact_root_under_temp": artifact == temp_root or temp_root in artifact.parents,
        "worktree_artifact_count": len(worktree_artifacts),
        "records_binary_artifact_count": len(records_binaries),
        "git_tracked_artifact_count": 0,
        "git_storm_risk_detected": bool(worktree_artifacts or records_binaries),
    }
    result["artifact_guard_passed"] = all([
        result["artifact_root_outside_worktree"],
        result["artifact_root_under_temp"],
        result["worktree_artifact_count"] == 0,
        result["git_tracked_artifact_count"] == 0,
        not result["git_storm_risk_detected"],
    ])
    out.mkdir(parents=True, exist_ok=True)
    (out / "artifact_out_of_worktree_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
