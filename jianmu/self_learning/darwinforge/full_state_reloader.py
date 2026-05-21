from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.full_root_state import FullRootState
from jianmu.self_learning.darwinforge.full_router_state import FullRouterState


def load_full_state(state_dir: str | Path) -> Dict[str, Any]:
    state_dir = Path(state_dir)
    manifest_path = state_dir / "full_state_manifest.json"
    if not manifest_path.exists():
        return {"state_loaded": False, "missing_state_files": ["full_state_manifest.json"], "load_warnings": ["missing manifest"]}
    manifest = _read_json(manifest_path)
    missing = [name for name in manifest.get("state_files", []) if not (state_dir / name).exists()]
    checksum = _compute_checksum(state_dir, manifest.get("state_files", [])) if not missing else ""
    checksum_match = checksum == manifest.get("checksum")
    schema_ok = manifest.get("state_version") == "v0.8.9.full_state"
    router = _read_json(state_dir / "full_router_state.json") if not missing else {}
    root = _read_json(state_dir / "full_root_state.json") if not missing else {}
    return {
        "state_loaded": not missing and checksum_match and schema_ok,
        "loaded_router_state": FullRouterState.from_dict(router).to_dict() if router else None,
        "loaded_root_state": FullRootState.from_dict(root).to_dict() if root else None,
        "loaded_boundary_probe_state": _read_json(state_dir / "boundary_probe_state.json") if (state_dir / "boundary_probe_state.json").exists() else None,
        "checksum_match": checksum_match,
        "schema_version_match": schema_ok,
        "missing_state_files": missing,
        "load_warnings": _warnings(manifest, missing, checksum_match, schema_ok),
        "persisted_state_support_level": manifest.get("persisted_state_support_level", "unavailable"),
        "state_manifest": manifest,
        "state_files": {
            "training_summary.json": {
                "summary": _read_json(Path(manifest.get("source_records_dir", "")) / "persisted_router_metrics.json")
            }
        },
    }


def _warnings(manifest: Dict[str, Any], missing: list[str], checksum_match: bool, schema_ok: bool) -> list[str]:
    warnings = []
    if missing:
        warnings.append("missing required state files")
    if not checksum_match:
        warnings.append("checksum mismatch")
    if not schema_ok:
        warnings.append("schema version mismatch")
    if manifest.get("persisted_state_support_level") != "full_router_root":
        warnings.append("support level is not full_router_root")
    return warnings


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_checksum(state_dir: Path, names: list[str]) -> str:
    import hashlib

    h = hashlib.sha256()
    for name in sorted(names):
        path = state_dir / name
        h.update(name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()
