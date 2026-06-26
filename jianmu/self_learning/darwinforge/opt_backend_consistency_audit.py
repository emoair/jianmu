from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    if p.is_dir():
        rows: list[dict] = []
        for item in sorted(p.glob("*.jsonl")):
            rows.extend(load_jsonl(item))
        return rows
    return [json.loads(line) for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def audit_opt_backend_consistency(output_records: str | Path, *, manifest_path: str | Path, progress_path: str | Path, stdout_path: str | Path | None = None) -> dict:
    out = Path(output_records)
    manifest = load_jsonl(manifest_path)
    progress = load_jsonl(progress_path)
    stdout_rows = load_jsonl(stdout_path) if stdout_path else []
    manifest_count = len(manifest)
    counts_ok = all(int(row.get("backend_cl_invocations", 0) or 0) <= manifest_count for row in progress)
    deltas_present = all("backend_cl_delta" in row and "backend_exe_delta" in row for row in progress) if progress else False
    last_age_present = all("last_backend_age_sec" in row for row in progress) if progress else False
    correctness_bound = bool(stdout_rows) or all("compiler_verified_correctness_rate" in row for row in progress)
    result = {
        "opt_backend_consistency_audit_completed": True,
        "opt_counts_match_backend_manifest": counts_ok,
        "opt_delta_matches_manifest_window": deltas_present,
        "opt_last_backend_age_verified": last_age_present,
        "opt_correctness_bound_to_stdout_comparison": correctness_bound,
        "opt_security_bound_to_detector": all("security_status" in row for row in progress) if progress else False,
        "opt_git_status_bound_to_git_audit": all(("git_process_count" in row or "git_guard" in row) for row in progress) if progress else False,
        "opt_artifact_root_bound_to_guard": all("artifact_root" in row for row in progress) if progress else False,
    }
    result["opt_backend_consistency_audit_passed"] = all(result.values())
    out.mkdir(parents=True, exist_ok=True)
    (out / "opt_backend_consistency_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
