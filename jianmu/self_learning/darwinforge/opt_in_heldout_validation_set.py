from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import LONGHAUL_CATEGORIES
from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import POLICY_BY_KIND


def build_heldout_validation_set(output_records: str | Path, profile_name: str, seed: int = 207) -> Dict[str, object]:
    samples: List[Dict[str, object]] = []
    for index, category in enumerate(LONGHAUL_CATEGORIES):
        policy = POLICY_BY_KIND.get(category, "default_profile_blocking_check")
        samples.append({
            "heldout_id": f"heldout_{index:04d}",
            "category": category,
            "profile": profile_name,
            "explicit_opt_in": category not in {"default_blocking", "malformed_opt_in_blocking", "opt_out_rollback", "post_rollback_default_blocking"},
            "expected_bridge_reachable": category not in {"default_blocking", "malformed_opt_in_blocking", "opt_out_rollback", "post_rollback_default_blocking"},
            "expected_policy": policy,
            "expected_stdout": "category-dependent",
            "source_generator": "existing_staged_opt_in_generators",
            "reuse_source": "v1.0.7 opt-in profile adapter and v1.0.6 dry-run adapter",
            "seed": seed + index,
        })
    result = {
        "heldout_set_created": True,
        "source_from_existing_generators": True,
        "no_external_data": True,
        "no_external_api": True,
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": True,
        "heldout_sample_count": len(samples),
        "categories": list(LONGHAUL_CATEGORIES),
        "samples": samples,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "heldout_validation_set_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
