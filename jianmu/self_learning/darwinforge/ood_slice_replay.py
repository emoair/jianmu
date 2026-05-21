from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


SOURCE_RECORD_PATHS = [
    "records/v0_8_1/ood_guard_stress.jsonl",
    "records/v0_8_1/ood_toxicity_by_class.json",
    "records/v0_8_1/ood_toxicity_longrun_metrics.json",
]


@dataclass(frozen=True)
class OODReplaySample:
    sample_id: str | None
    raw_text: str | None
    canonical_text: str | None
    ood_class: str | None
    accepted_as_supported: bool | None
    rejection_layer: str | None
    false_accept_reason: str | None
    original_record_path: str
    original_run_id: str | None
    source_branch: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def load_v081_ood_slice(repo_root: str | Path, source_branch: str = "v0.8.1-ood-toxicity-longrun-scale") -> Dict:
    repo_root = Path(repo_root)
    loaded: List[Dict] = []
    source_paths = []
    missing_sources = []
    partial_replay = False
    for relpath in SOURCE_RECORD_PATHS:
        text = _read_from_worktree_or_branch(repo_root, relpath, source_branch)
        if text is None:
            missing_sources.append(relpath)
            continue
        source_paths.append(relpath)
        if relpath.endswith(".jsonl"):
            for line in text.splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                loaded.append(_row_to_sample(row, relpath, source_branch).to_dict())
        else:
            # Summary JSON is useful provenance, but it does not make replay
            # partial when the raw JSONL slice was also loaded.
            continue
    missing_field_counts = _missing_field_counts(loaded)
    if missing_field_counts.get("raw_text", 0):
        partial_replay = True
    return {
        "records": loaded,
        "replay_sample_count": len(loaded),
        "partial_replay": partial_replay,
        "missing_field_counts": missing_field_counts,
        "source_branch": source_branch,
        "source_record_paths": source_paths,
        "missing_sources": missing_sources,
    }


def _row_to_sample(row: Dict, relpath: str, source_branch: str) -> OODReplaySample:
    return OODReplaySample(
        sample_id=row.get("sample_id"),
        raw_text=row.get("raw_text"),
        canonical_text=row.get("canonical_text"),
        ood_class=row.get("ood_class"),
        accepted_as_supported=row.get("accepted_as_supported"),
        rejection_layer=row.get("rejection_layer"),
        false_accept_reason=row.get("false_accept_reason"),
        original_record_path=relpath,
        original_run_id=row.get("run_id"),
        source_branch=source_branch,
    )


def _read_from_worktree_or_branch(repo_root: Path, relpath: str, source_branch: str) -> str | None:
    local_path = repo_root / relpath
    if local_path.exists():
        return local_path.read_text(encoding="utf-8")
    ref = f"{source_branch}:{relpath}"
    proc = subprocess.run(["git", "show", ref], cwd=repo_root, text=True, capture_output=True, encoding="utf-8")
    if proc.returncode != 0:
        return None
    return proc.stdout


def _missing_field_counts(rows: List[Dict]) -> Dict[str, int]:
    fields = ["sample_id", "raw_text", "canonical_text", "ood_class", "accepted_as_supported", "false_accept_reason"]
    return {field: sum(1 for row in rows if row.get(field) in (None, "")) for field in fields}
