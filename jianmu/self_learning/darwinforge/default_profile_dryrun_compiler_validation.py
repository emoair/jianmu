from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.layerwise_profile_compiler_validation import run_layerwise_profile_compiler_validation


COMPILER_PROFILE_MAP = {
    "actual_current_default_reference": "current_1B_reference",
    "current_1B_reference": "current_1B_reference",
    "combined_hot_rebalanced_balanced_sampling_1B": "combined_hot_rebalanced_balanced_sampling_1B",
    "layerwise_sparse_1B_freeze_prune_dryrun_default": "layerwise_sparse_1B_freeze_prune",
}


def run_default_dryrun_compiler_validation(
    frontier_dataset_dir: str | Path,
    output_records: str | Path,
    profiles: Iterable[str],
    compile_worker_count: int = 16,
    supported_samples: int = 3000,
    boundary_samples: int = 3000,
    seed: int = 95,
) -> Dict[str, Any]:
    mapped = []
    for profile in profiles:
        target = COMPILER_PROFILE_MAP.get(profile, profile)
        if target not in mapped:
            mapped.append(target)
    raw = run_layerwise_profile_compiler_validation(frontier_dataset_dir, output_records, mapped, compile_worker_count, supported_samples, boundary_samples, 5, seed)
    per_profile: Dict[str, Any] = {}
    for profile in profiles:
        target = COMPILER_PROFILE_MAP.get(profile, profile)
        if target in raw.get("per_profile", {}):
            per_profile[profile] = dict(raw["per_profile"][target])
    layerwise = per_profile.get("layerwise_sparse_1B_freeze_prune_dryrun_default", raw.get("per_profile", {}).get("layerwise_sparse_1B_freeze_prune", {}))
    result = dict(raw)
    result["per_profile"] = per_profile
    result["compiler_verified_correct_rate"] = layerwise.get("compiler_verified_correct_rate", 0.0)
    result["permission_error_count"] = layerwise.get("permission_error_count", 0)
    result["cleanup_failure_count"] = layerwise.get("cleanup_failure_count", 0)
    result["process_spawn_error_count"] = layerwise.get("process_spawn_error_count", 0)
    result["timeout_count"] = layerwise.get("timeout_count", 0)
    result["wrong_stdout_count"] = layerwise.get("wrong_stdout_count", 0)
    result["boundary_compiler_misroute_count"] = layerwise.get("boundary_compiler_misroute_count", 0)
    result["future_domain_compiled_count"] = layerwise.get("future_domain_compiled_count", 0)
    result["recursion_compiled_count"] = layerwise.get("recursion_compiled_count", 0)
    result["array_compiled_count"] = layerwise.get("array_compiled_count", 0)
    result["function_compiled_count"] = layerwise.get("function_compiled_count", 0)
    Path(output_records, "compiler_validation_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
