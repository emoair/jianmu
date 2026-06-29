from __future__ import annotations

import json
from pathlib import Path


def run_dataset_artifact_hygiene_guard(output_records: str | Path, dataset_artifact_root: str | Path) -> dict:
    root = Path(dataset_artifact_root)
    cwd = Path.cwd().resolve()
    outside = not (root.resolve() == cwd or cwd in root.resolve().parents)
    result = {
        "repo_hygiene_guard_completed": True,
        "dataset_artifacts_outside_worktree": outside,
        "worktree_dataset_artifacts_detected": any(Path(".").glob("dataset_manifest.*.jsonl")),
        "git_index_lock_detected": Path(".git/index.lock").exists(),
        "repo_hygiene_guard_passed": outside and not Path(".git/index.lock").exists(),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "repo_hygiene_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
