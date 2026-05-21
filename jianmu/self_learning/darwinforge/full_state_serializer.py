from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.full_root_state import FullRootState
from jianmu.self_learning.darwinforge.full_router_state import FullRouterState
from jianmu.self_learning.darwinforge.persisted_router_state import FORBIDDEN_STATE_FIELDS, find_forbidden_fields_in_state
from jianmu.self_learning.darwinforge.state_inventory_audit import run_state_inventory_audit, write_state_inventory


@dataclass(frozen=True)
class FullStateManifest:
    state_version: str
    persisted_state_support_level: str
    source_branch: str
    source_records_dir: str
    created_at: str
    seed: int
    state_files: List[str]
    checksum: str
    forbidden_fields_excluded: bool
    state_inventory_summary: Dict[str, Any]
    arxiv_blocking_if_not_full: bool


def save_full_state(source_records_dir: str | Path, state_dir: str | Path, seed: int = 42, source_branch: str = "v0.8.8-persisted-router-external-ood") -> Dict[str, Any]:
    source_records_dir = Path(source_records_dir)
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    inventory = run_state_inventory_audit(source_records_dir)
    router = FullRouterState.from_available_runtime(seed=seed, source_config={"source_records_dir": str(source_records_dir)})
    root = FullRootState.from_available_runtime(seed=seed, source_config={"source_records_dir": str(source_records_dir)})
    boundary_probe_state = {
        "schema_version": "v0.8.9.boundary_probe_state",
        "evaluation_only": True,
        "source_records_dir": str(source_records_dir),
        "summary_files": _summary_files(source_records_dir),
    }
    support_level = _support_level(inventory)
    payloads = {
        "full_router_state.json": router.to_dict(),
        "full_root_state.json": root.to_dict(),
        "boundary_probe_state.json": boundary_probe_state,
    }
    for name, payload in payloads.items():
        _write_json(state_dir / name, payload)
    write_state_inventory(state_dir / "state_inventory.json", inventory)
    forbidden_scan = scan_state_for_forbidden_fields(state_dir, list(payloads) + ["state_inventory.json"])
    _write_json(state_dir / "forbidden_field_scan.json", forbidden_scan)
    files = list(payloads) + ["state_inventory.json", "forbidden_field_scan.json"]
    checksum = _compute_checksum(state_dir, files)
    manifest = FullStateManifest(
        state_version="v0.8.9.full_state",
        persisted_state_support_level=support_level,
        source_branch=source_branch,
        source_records_dir=str(source_records_dir),
        created_at=datetime.now(timezone.utc).isoformat(),
        seed=seed,
        state_files=files,
        checksum=checksum,
        forbidden_fields_excluded=forbidden_scan["forbidden_field_in_state_count"] == 0,
        state_inventory_summary={
            "inventory_passed": inventory["inventory_passed"],
            "serializable_component_count": inventory["serializable_component_count"],
            "missing_for_full_state": inventory["missing_for_full_state"],
        },
        arxiv_blocking_if_not_full=support_level != "full_router_root",
    )
    _write_json(state_dir / "full_state_manifest.json", asdict(manifest))
    (state_dir / "state_checksum.txt").write_text(checksum + "\n", encoding="utf-8")
    return {
        "state_saved": True,
        "state_manifest_path": str(state_dir / "full_state_manifest.json"),
        "persisted_state_support_level": support_level,
        "state_checksum": checksum,
        "inventory": inventory,
        **forbidden_scan,
    }


def scan_state_for_forbidden_fields(state_dir: str | Path, state_files: Iterable[str] | None = None) -> Dict[str, Any]:
    state_dir = Path(state_dir)
    names = list(state_files) if state_files is not None else [p.name for p in state_dir.glob("*.json")]
    combined: Dict[str, Any] = {}
    for name in names:
        path = state_dir / name
        if path.exists():
            combined[name] = json.loads(path.read_text(encoding="utf-8"))
    result = find_forbidden_fields_in_state(combined)
    result["scanned_files"] = names
    result["forbidden_field_names"] = sorted(FORBIDDEN_STATE_FIELDS)
    return result


def _support_level(inventory: Dict[str, Any]) -> str:
    missing = inventory.get("missing_for_full_state", [])
    if not missing:
        return "full_router_root"
    has_router_schema = inventory.get("branchchain_state_found") and inventory.get("branch_neuron_state_found")
    has_root_schema = inventory.get("root_colony_state_found") and inventory.get("root_lifecycle_state_found")
    if has_router_schema and has_root_schema:
        return "partial"
    if has_router_schema:
        return "router_only"
    if has_root_schema:
        return "root_only"
    return "summary_only"


def _summary_files(source_records_dir: Path) -> List[str]:
    return sorted(str(path.name) for path in source_records_dir.glob("*.json")) if source_records_dir.exists() else []


def _compute_checksum(state_dir: Path, names: Iterable[str]) -> str:
    h = hashlib.sha256()
    for name in sorted(names):
        path = state_dir / name
        h.update(name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
