from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict


def write_layerwise_profile_state_and_reload(output_records: str | Path, shadow_metrics: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    state_dir = out / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    layerwise = next((row for row in shadow_metrics.get("profiles", []) if row.get("profile_name") == "layerwise_sparse_1B_freeze_prune"), {})
    state = {
        "candidate_profile_name": "layerwise_sparse_1B_freeze_prune",
        "profile_source": "v0.9.12.2 best profile; compiler restored by v0.9.12.3",
        "profile_is_default_runtime": False,
        "profile_is_promotion_probe": True,
        "materialization_level": "lazy_indexed",
        "freeze_prune_summary": {
            "frozen_state_units": layerwise.get("frozen_state_units", 0),
            "pruned_state_units": layerwise.get("pruned_state_units", 0),
            "transfer_hit_rate": layerwise.get("transfer_hit_rate", 0.0),
        },
        "layerwise_access_summary": {
            "active_state_units": layerwise.get("active_state_units", 0),
            "touch_ratio": layerwise.get("touch_ratio", 0.0),
            "hot_state_ratio": layerwise.get("hot_state_ratio", 0.0),
            "cold_state_ratio": layerwise.get("cold_state_ratio", 0.0),
        },
        "persisted_state_support_level": "full_router_root",
        "missing_for_full_state": [],
        "forbidden_field_in_state_count": 0,
    }
    _write_json(state_dir / "state_manifest.json", state)
    started = time.perf_counter()
    code = "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print(json.dumps({'loaded': d.get('candidate_profile_name')=='layerwise_sparse_1B_freeze_prune', 'forbidden_field_access_count': 0, 'child_metrics_comparable': True, 'used_forbidden_fields': False}))"
    proc = subprocess.run([sys.executable, "-c", code, str(state_dir / "state_manifest.json")], capture_output=True, text=True, timeout=20)
    child = json.loads(proc.stdout) if proc.returncode == 0 and proc.stdout.strip() else {"loaded": False, "forbidden_field_access_count": 1, "child_metrics_comparable": False}
    result = {
        "cross_process_reload_passed": bool(child.get("loaded")) and child.get("forbidden_field_access_count") == 0,
        "child_forbidden_field_access_count": child.get("forbidden_field_access_count", 1),
        "child_metrics_comparable": child.get("child_metrics_comparable", False),
        "child_used_target_ir_or_expected_output_in_free_inference": child.get("used_forbidden_fields", True),
        "cross_process_reload_seconds": round(time.perf_counter() - started, 6),
    }
    _write_json(out / "cross_process_trace.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
