from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_default_profile_dryrun_config(output_records: str | Path) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "actual_default_profile_name": "actual_current_default_reference",
        "dry_run_default_profile_name": "layerwise_sparse_1B_freeze_prune",
        "actual_default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "profile_is_default_runtime": False,
        "dry_run_mode_enabled": True,
        "fallback_profile_name": "combined_hot_rebalanced_balanced_sampling_1B",
        "rollback_profile_name": "actual_current_default_reference",
        "profile_source": "v0.9.13 layerwise profile promotion probe passed",
        "materialization_level": "lazy_indexed",
        "freeze_prune_enabled": True,
        "layerwise_enabled": True,
        "default_config_path_touched": "shadow_only",
        "production_config_modified": False,
    }
    _write_json(out / "default_profile_dryrun_config.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
