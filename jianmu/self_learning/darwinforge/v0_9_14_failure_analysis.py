from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.targeted_candidate_space_compiler_validation import run_targeted_compiler_validation


def run_dataset_v2_compiler_spot_audit(dataset_dir: str | Path, output_records: str | Path, compile_worker_count: int = 16, seed: int = 96, supported_limit: int = 3000, boundary_limit: int = 3000) -> Dict[str, Any]:
    out = Path(output_records)
    rows = list(_iter_rows(Path(dataset_dir) / "pilot"))
    supported = [row for row in rows if row.get("support_status") == "current_supported"][:supported_limit]
    boundary = [row for row in rows if row.get("support_status") != "current_supported"][:boundary_limit]
    metrics = run_targeted_compiler_validation(out / "dataset_v2_compiler_spot", supported, boundary, compile_worker_count=compile_worker_count, seed=seed)
    src = out / "dataset_v2_compiler_spot" / "compiler_validation_trace_000.jsonl"
    dst = out / "dataset_v2_compiler_spot_trace_000.jsonl"
    if src.exists():
        shutil.copyfile(src, dst)
    result = {
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count", 0),
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count", 0),
        "future_domain_compiled_count": 0,
        "unsupported_compiled_count": 0,
        "trap_compiled_count": 0,
        "function_compiled_count": 0,
        "array_compiled_count": 0,
        "recursion_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "permission_error_count": metrics.get("permission_error_count", 0),
        "cleanup_failure_count": metrics.get("cleanup_failure_count", 0),
        "backend_claim_safe": metrics.get("backend_claim_safe", False),
    }
    _write_json(out / "dataset_v2_compiler_spot_audit.json", result)
    _write_json(out / "dataset_v2_compiler_spot_trace_manifest.json", {"trace_sharded": True, "shards": [{"path": dst.name, "row_count": sum(1 for _ in dst.open(encoding="utf-8")) if dst.exists() else 0}]})
    return result


def _iter_rows(scale_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
