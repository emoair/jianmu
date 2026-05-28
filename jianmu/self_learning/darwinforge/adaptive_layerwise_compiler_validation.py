from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.targeted_candidate_space_compiler_validation import run_targeted_compiler_validation


VALIDATED_PROFILES = ["current_1B_reference", "combined_hot_rebalanced_balanced_sampling_1B", "layerwise_sparse_1B_freeze_prune"]


def run_adaptive_layerwise_compiler_validation(output_records: str | Path, profile_samples: Dict[str, Dict[str, List[Dict[str, Any]]]], compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    per_profile: Dict[str, Any] = {}
    manifest = {"trace_sharded": True, "validated_profiles": [], "shards": []}
    for profile_name in VALIDATED_PROFILES:
        if profile_name not in profile_samples:
            continue
        samples = profile_samples[profile_name]
        profile_dir = out / "compiler_validation" / profile_name
        metrics = run_targeted_compiler_validation(profile_dir, samples["supported"][:1500], samples["boundary"][:1500], compile_worker_count=compile_worker_count)
        per_profile[profile_name] = metrics
        shard_src = profile_dir / "compiler_validation_trace_000.jsonl"
        shard_name = f"compiler_validation_trace_{profile_name}.jsonl"
        shard_dst = out / shard_name
        shard_dst.write_text(shard_src.read_text(encoding="utf-8"), encoding="utf-8")
        manifest["validated_profiles"].append(profile_name)
        manifest["shards"].append({"profile_name": profile_name, "path": shard_name, "row_count": sum(1 for _ in shard_dst.open(encoding="utf-8"))})
    result = {
        "compiler_validation_completed": bool(per_profile),
        "compile_worker_count": compile_worker_count,
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compiler_environment": "msvc_vcvars64",
        "per_profile": per_profile,
        "real_compiler_invocation_count": sum(row.get("real_compiler_invocation_count", 0) for row in per_profile.values()),
        "compiler_verified_correct_rate_best": min((row.get("compiler_verified_correct_rate", 0.0) for row in per_profile.values()), default=0.0),
        "boundary_compiler_misroute_count_best": sum(row.get("boundary_compiler_misroute_count", 0) for row in per_profile.values()),
        "future_domain_compiled_count": sum(row.get("future_domain_compiled_count", 0) for row in per_profile.values()),
        "recursion_compiled_count": sum(row.get("recursion_compiled_count", 0) for row in per_profile.values()),
        "array_compiled_count": sum(row.get("array_compiled_count", 0) for row in per_profile.values()),
        "function_compiled_count": sum(row.get("function_compiled_count", 0) for row in per_profile.values()),
        "permission_error_count": sum(row.get("permission_error_count", 0) for row in per_profile.values()),
        "cleanup_failure_count": sum(row.get("cleanup_failure_count", 0) for row in per_profile.values()),
        "timeout_count": sum(row.get("timeout_count", 0) for row in per_profile.values()),
        "backend_claim_safe": all(row.get("backend_claim_safe", False) for row in per_profile.values()) if per_profile else False,
    }
    _write_json(out / "compiler_validation_metrics.json", result)
    _write_json(out / "compiler_validation_trace_manifest.json", manifest)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
