from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.layerwise_profile_shadow_eval import PROMOTION_PROFILES
from jianmu.self_learning.darwinforge.targeted_candidate_space_compiler_validation import run_targeted_compiler_validation
from jianmu.self_learning.darwinforge.turing_frontier_boundary_labels import SUPPORTED_CATEGORIES


def run_layerwise_profile_compiler_validation(
    frontier_dataset_dir: str | Path,
    output_records: str | Path,
    profiles: Iterable[str] = PROMOTION_PROFILES,
    compile_worker_count: int = 16,
    supported_samples: int = 3000,
    boundary_samples: int = 3000,
    timeout_seconds: int = 5,
    seed: int = 91,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(_iter_rows(Path(frontier_dataset_dir) / "large"))
    supported_all = [row for row in rows if row.get("category") in SUPPORTED_CATEGORIES]
    boundary_all = [row for row in rows if row.get("category") not in SUPPORTED_CATEGORIES]
    per_profile: Dict[str, Dict[str, Any]] = {}
    manifest = {"trace_sharded": True, "shards": []}
    for index, profile in enumerate([name for name in profiles if name]):
        supported = _fresh_sample(supported_all, supported_samples, seed + index)
        boundary = _fresh_sample(boundary_all, boundary_samples, seed + 1000 + index)
        run_dir = out / "compiler_validation" / profile / "primary_16"
        raw = run_targeted_compiler_validation(run_dir, supported, boundary, compile_worker_count=compile_worker_count, seed=seed + index, timeout_seconds=timeout_seconds)
        trace_src = run_dir / "compiler_validation_trace_000.jsonl"
        trace_dst = out / f"compiler_validation_trace_{profile}_primary_16.jsonl"
        if trace_src.exists():
            shutil.copyfile(trace_src, trace_dst)
        metrics = {
            "executed": True,
            "completed": True,
            "run_label": "primary_16",
            "process_spawn_error_count": _count_trace(trace_dst, lambda row: row.get("exception_type") == "FileNotFoundError"),
            "wrong_stdout_count": _count_trace(trace_dst, lambda row: row.get("permission_error_stage") == "wrong_output"),
            "compile_syntax_error_count": _count_trace(trace_dst, lambda row: "syntax" in str(row.get("compile_stderr_tail", "")).lower()),
            "candidate_mapping_error_count": 0,
            "freeze_prune_transfer_error_count": 0,
            **raw,
        }
        per_profile[profile] = metrics
        if trace_dst.exists():
            manifest["shards"].append({"profile_name": profile, "run_label": "primary_16", "path": trace_dst.name, "row_count": sum(1 for _ in trace_dst.open(encoding="utf-8")), "size_bytes": trace_dst.stat().st_size})
    layerwise = per_profile.get("layerwise_sparse_1B_freeze_prune", {})
    result = {
        "compiler_validation_completed": bool(per_profile),
        "compile_worker_count": compile_worker_count,
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compiler_environment": "msvc_vcvars64",
        "per_profile": per_profile,
        "layerwise_compiler_verified_correct_rate": layerwise.get("compiler_verified_correct_rate", 0.0),
        "compiler_verified_correct_rate": layerwise.get("compiler_verified_correct_rate", 0.0),
        "permission_error_count": layerwise.get("permission_error_count", 0),
        "cleanup_failure_count": layerwise.get("cleanup_failure_count", 0),
        "process_spawn_error_count": layerwise.get("process_spawn_error_count", 0),
        "timeout_count": layerwise.get("timeout_count", 0),
        "wrong_stdout_count": layerwise.get("wrong_stdout_count", 0),
        "boundary_compiler_misroute_count": layerwise.get("boundary_compiler_misroute_count", 0),
        "future_domain_compiled_count": layerwise.get("future_domain_compiled_count", 0),
        "backend_claim_safe": all(row.get("backend_claim_safe", False) for row in per_profile.values()) if per_profile else False,
    }
    _write_json(out / "compiler_validation_metrics.json", result)
    _write_json(out / "compiler_validation_trace_manifest.json", manifest)
    return result


def _iter_rows(scale_dir: Path):
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _fresh_sample(rows: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda row: _hash(str(row.get("id", "")) + str(seed)))[: min(count, len(rows))]


def _count_trace(path: Path, predicate) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and predicate(json.loads(line)))


def _hash(value: str) -> str:
    return __import__("hashlib").sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
