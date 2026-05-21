from __future__ import annotations

import hashlib
import json
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
}


def build_runtime_full_state(runtime_capture: Dict[str, Any], output_dir: str | Path, source_branch: str = "v0.9.0-runtime-state-capture-figures", seed: int = 42) -> Dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    components = {
        "trained_branch_population": runtime_capture.get("trained_branch_population"),
        "trained_root_colonies": runtime_capture.get("trained_root_colonies"),
        "lifecycle_runtime_states": runtime_capture.get("lifecycle_runtime_states"),
        "nutrient_toxic_runtime_memory": runtime_capture.get("nutrient_toxic_runtime_memory"),
    }
    missing = [name for name, payload in components.items() if not payload]
    forbidden_scan = scan_forbidden_fields(components)
    support_level = "full_router_root" if not missing and forbidden_scan["forbidden_field_in_state_count"] == 0 else "partial"
    inventory = {
        "runtime_capture_passed": runtime_capture.get("runtime_capture_passed", False),
        "trained_branch_population_captured": bool(components["trained_branch_population"]),
        "trained_root_colonies_captured": bool(components["trained_root_colonies"]),
        "lifecycle_states_captured": bool(components["lifecycle_runtime_states"]),
        "nutrient_toxic_memory_captured": bool(components["nutrient_toxic_runtime_memory"]),
        "serializable_component_count": sum(1 for payload in components.values() if payload),
        "missing_for_full_state": missing,
        "inventory_passed": not missing,
    }
    checksums = {}
    file_map = {
        "trained_branch_population.json": components["trained_branch_population"] or {},
        "trained_root_colonies.json": components["trained_root_colonies"] or {},
        "lifecycle_runtime_states.json": components["lifecycle_runtime_states"] or {},
        "nutrient_toxic_runtime_memory.json": components["nutrient_toxic_runtime_memory"] or {},
        "runtime_state_inventory.json": inventory,
        "forbidden_field_scan.json": forbidden_scan,
    }
    for filename, payload in file_map.items():
        _write_json(output / filename, payload)
        checksums[filename] = _hash_payload(payload)
    manifest = {
        "state_version": "v0.9.0.runtime_full_state",
        "persisted_state_support_level": support_level,
        "source_branch": source_branch,
        "source_records_dir": str(Path(output).parents[0]) if output.name == "state" else str(output),
        "seed": seed,
        "state_files": sorted(file_map),
        "checksums": checksums,
        "checksum": _hash_payload({"checksums": checksums, "support_level": support_level}),
        "forbidden_fields_excluded": sorted(FORBIDDEN_STATE_FIELDS),
        "forbidden_field_in_state_count": forbidden_scan["forbidden_field_in_state_count"],
        "missing_for_full_state": missing,
        "full_state_ready": support_level == "full_router_root",
        "arxiv_blocking_if_not_full": support_level != "full_router_root",
    }
    _write_json(output / "runtime_full_state_manifest.json", manifest)
    (output / "state_checksum.txt").write_text(manifest["checksum"] + "\n", encoding="utf-8")
    return {
        "persisted_state_support_level": support_level,
        "missing_for_full_state": missing,
        "full_state_ready": support_level == "full_router_root",
        "forbidden_field_in_state_count": forbidden_scan["forbidden_field_in_state_count"],
        "manifest": manifest,
        "state_manifest_path": str(output / "runtime_full_state_manifest.json"),
        "inventory": inventory,
        "forbidden_scan": forbidden_scan,
    }


def load_runtime_full_state(state_dir: str | Path) -> Dict[str, Any]:
    state = Path(state_dir)
    manifest_path = state / "runtime_full_state_manifest.json"
    manifest = _read_json(manifest_path)
    files = {}
    missing = []
    checksum_mismatch = []
    for filename in manifest.get("state_files", []):
        path = state / filename
        if not path.exists():
            missing.append(filename)
            continue
        payload = _read_json(path)
        files[filename] = payload
        expected = manifest.get("checksums", {}).get(filename)
        if expected and expected != _hash_payload(payload):
            checksum_mismatch.append(filename)
    return {
        "state_loaded": not missing and not checksum_mismatch,
        "persisted_state_support_level": manifest.get("persisted_state_support_level", "unavailable"),
        "manifest": manifest,
        "state_files": files,
        "checksum_match": not checksum_mismatch,
        "missing_state_files": missing,
        "checksum_mismatch_files": checksum_mismatch,
    }


def scan_forbidden_fields(payload: Any) -> Dict[str, Any]:
    seen: List[str] = []
    examples: List[str] = []
    _scan(payload, path="$", seen=seen, examples=examples)
    return {
        "forbidden_field_in_state_count": len(seen),
        "forbidden_fields_in_state": sorted(set(seen)),
        "violation_examples": examples[:20],
        "forbidden_field_scan_passed": len(seen) == 0,
    }


def _scan(payload: Any, path: str, seen: List[str], examples: List[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_s = str(key)
            child = f"{path}.{key_s}"
            if key_s in FORBIDDEN_STATE_FIELDS:
                seen.append(key_s)
                examples.append(child)
            _scan(value, child, seen, examples)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _scan(value, f"{path}[{index}]", seen, examples)


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _hash_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
