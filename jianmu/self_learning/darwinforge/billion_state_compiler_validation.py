from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.targeted_candidate_space_compiler_validation import run_targeted_compiler_validation


def run_billion_state_compiler_validation(
    output_records: str | Path,
    profile_samples: Dict[str, Dict[str, List[Dict[str, Any]]]],
    compile_worker_count: int = 16,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    per_profile: Dict[str, Any] = {}
    manifest = {"trace_sharded": True, "shards": [], "per_profile": {}}
    for profile_name, samples in profile_samples.items():
        profile_dir = out / "compiler_validation" / profile_name
        metrics = run_targeted_compiler_validation(profile_dir, samples["supported"][:1500], samples["boundary"][:1500], compile_worker_count=compile_worker_count)
        per_profile[profile_name] = metrics
        shard_src = profile_dir / "compiler_validation_trace_000.jsonl"
        shard_name = f"compiler_validation_trace_{profile_name}.jsonl"
        shard_dst = out / shard_name
        shard_dst.write_text(shard_src.read_text(encoding="utf-8"), encoding="utf-8")
        manifest["shards"].append({"profile_name": profile_name, "path": shard_name, "row_count": sum(1 for _ in shard_dst.open(encoding="utf-8"))})
        manifest["per_profile"][profile_name] = metrics
    result = {"compiler_validation_completed": True, "compile_worker_count": compile_worker_count, "per_profile": per_profile}
    (out / "compiler_validation_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "compiler_validation_trace_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

