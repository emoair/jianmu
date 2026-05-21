from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


FORBIDDEN_STATE_FIELDS = {
    "boundary_label",
    "expected_action",
    "nutrient_policy",
    "toxicity_policy",
    "target_ir",
    "expected_output",
    "target_branch_path",
    "current_support_status",
    "future_support_status",
}


@dataclass(frozen=True)
class PersistedStateManifest:
    state_version: str
    source_branch: str
    source_records_dir: str
    created_at: str
    seed: int
    state_files: List[str]
    checksum: str
    includes_branch_state: bool
    includes_root_state: bool
    includes_boundary_probe_state: bool
    includes_training_summary: bool
    forbidden_fields_excluded: bool
    persisted_state_support_level: str


def save_persisted_router_state(
    source_records_dir: str | Path,
    output_state_dir: str | Path,
    seed: int = 42,
    source_branch: str = "v0.8.7-boundary-freebeam-generalization",
) -> Dict[str, Any]:
    """Persist the currently available state honestly.

    JianMu v0.8.7 exposes probe/free-beam summaries, not a complete BranchChain/root
    state object. The saved state is therefore marked summary_only.
    """

    source_records_dir = Path(source_records_dir)
    output_state_dir = Path(output_state_dir)
    output_state_dir.mkdir(parents=True, exist_ok=True)

    training_summary = _read_json(source_records_dir / "freebeam_boundary_metrics.json")
    freebeam_summary = _read_json(source_records_dir / "boundary_generalization_metrics.json")
    guard_summary = _read_json(source_records_dir / "no_label_inference_guard.json")

    state_payloads = {
        "training_summary.json": {
            "evaluation_only": True,
            "source": "records/v0_8_7/freebeam_boundary_metrics.json",
            "summary": _strip_forbidden(training_summary),
        },
        "freebeam_summary.json": {
            "evaluation_only": True,
            "source": "records/v0_8_7/boundary_generalization_metrics.json",
            "summary": _strip_forbidden(freebeam_summary),
        },
        "no_label_guard_config.json": {
            "evaluation_only": True,
            "source": "records/v0_8_7/no_label_inference_guard.json",
            "summary": _strip_forbidden(guard_summary),
            "forbidden_fields_excluded": True,
        },
    }

    state_files: List[str] = []
    for name, payload in state_payloads.items():
        _write_json(output_state_dir / name, payload)
        state_files.append(name)

    checksum = _compute_checksum(output_state_dir, state_files)
    forbidden = find_forbidden_fields_in_state({"files": state_payloads})
    manifest = PersistedStateManifest(
        state_version="v0.8.8-summary-state",
        source_branch=source_branch,
        source_records_dir=str(source_records_dir),
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=seed,
        state_files=state_files,
        checksum=checksum,
        includes_branch_state=False,
        includes_root_state=False,
        includes_boundary_probe_state=True,
        includes_training_summary=True,
        forbidden_fields_excluded=forbidden["forbidden_field_in_state_count"] == 0,
        persisted_state_support_level="summary_only",
    )
    _write_json(output_state_dir / "state_manifest.json", asdict(manifest))
    (output_state_dir / "state_checksum.txt").write_text(checksum + "\n", encoding="utf-8")

    return {
        "state_saved": True,
        "state_loaded": False,
        "state_manifest_path": str(output_state_dir / "state_manifest.json"),
        "state_checksum": checksum,
        "persisted_state_support_level": "summary_only",
        **forbidden,
    }


def load_persisted_router_state(state_dir: str | Path) -> Dict[str, Any]:
    state_dir = Path(state_dir)
    manifest_path = state_dir / "state_manifest.json"
    manifest = _read_json(manifest_path)
    files = {name: _read_json(state_dir / name) for name in manifest.get("state_files", [])}
    checksum = _compute_checksum(state_dir, manifest.get("state_files", []))
    forbidden = find_forbidden_fields_in_state({"manifest": manifest, "files": files})
    return {
        "state_loaded": True,
        "state_manifest": manifest,
        "state_files": files,
        "state_checksum": checksum,
        "checksum_matches_manifest": checksum == manifest.get("checksum"),
        "persisted_state_support_level": manifest.get("persisted_state_support_level", "unavailable"),
        **forbidden,
    }


def find_forbidden_fields_in_state(data: Any) -> Dict[str, Any]:
    found: List[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in FORBIDDEN_STATE_FIELDS:
                    found.append(key)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return {
        "forbidden_field_in_state_count": len(found),
        "forbidden_fields_in_state": sorted(set(found)),
    }


def _strip_forbidden(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_forbidden(child) for key, child in value.items() if key not in FORBIDDEN_STATE_FIELDS}
    if isinstance(value, list):
        return [_strip_forbidden(child) for child in value]
    return value


def _compute_checksum(state_dir: Path, names: Iterable[str]) -> str:
    h = hashlib.sha256()
    for name in sorted(names):
        path = state_dir / name
        h.update(name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"available": False, "missing_path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
