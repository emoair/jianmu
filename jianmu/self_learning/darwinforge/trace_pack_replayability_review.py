from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend
from jianmu.self_learning.darwinforge.production_profile_interface_adapter import execute_shadow_profile_request


POLICY_TO_KIND = {
    "canonical_arithmetic_targetir": "arithmetic",
    "canonical_function_targetir": "function",
    "canonical_array_targetir": "array",
    "canonical_function_array_targetir": "function_array",
    "canonical_structured_recursion_targetir": "structured_recursion",
    "mixed_extended_ir_path": "mixed",
}


def run_trace_pack_replayability_review(source_records: str | Path, output_records: str | Path, replay_samples: int = 2000, workers: int = 16, compiler_workers: int = 16) -> Dict[str, object]:
    source_rows = _select_samples(Path(source_records) / "dry_run_trace_pack", replay_samples)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    workers_used = max(1, min(workers, compiler_workers, 16))
    replay_rows: List[Dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers_used) as pool:
        futures = [pool.submit(_replay_one, row, backend) for row in source_rows]
        for future in as_completed(futures):
            replay_rows.append(future.result())
    replay_rows.sort(key=lambda row: str(row["dry_run_sample_id"]))
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "trace_replay_manifest.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in replay_rows), encoding="utf-8")
    policies = {row["policy"] for row in replay_rows}
    result = {
        "trace_replay_completed": True,
        "replay_sample_count": len(replay_rows),
        "replay_success_rate": round(sum(1 for row in replay_rows if row["replay_passed"]) / len(replay_rows), 6) if replay_rows else 0.0,
        "replay_fail_count": sum(1 for row in replay_rows if not row["replay_passed"]),
        "replay_stdout_mismatch_count": sum(1 for row in replay_rows if row["stdout_mismatch"]),
        "replay_source_hash_drift_count": sum(1 for row in replay_rows if row["source_hash_drift"]),
        "replay_policy_path_drift_count": sum(1 for row in replay_rows if row["policy_path_drift"]),
        "replay_ir_kind_drift_count": sum(1 for row in replay_rows if row["ir_kind_drift"]),
        "replay_compile_failure_count": sum(1 for row in replay_rows if row["compile_failure"]),
        "replay_timeout_count": sum(1 for row in replay_rows if row["timeout"]),
        "replay_all_policies_covered": set(POLICY_TO_KIND) <= policies,
        "trace_pack_replayability_passed": bool(replay_rows) and all(row["replay_passed"] for row in replay_rows) and set(POLICY_TO_KIND) <= policies,
        "workers_requested": workers,
        "workers_used": workers_used,
        "downgrade_reason": "" if workers_used == workers else "capped_for_thread_safe_local_compiler_replay",
    }
    _write_json(out / "trace_pack_replayability_review.json", result)
    return result


def _select_samples(pack: Path, count: int) -> List[Dict[str, Any]]:
    rows = list(_iter_policy_rows(pack))
    by_policy: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_policy.setdefault(str(row["policy"]), []).append(row)
    selected: List[Dict[str, Any]] = []
    per_policy = max(1, count // max(1, len(by_policy)))
    for policy in sorted(by_policy):
        selected.extend(by_policy[policy][:per_policy])
    index = 0
    while len(selected) < count and rows:
        selected.append(rows[index % len(rows)])
        index += 1
    return selected[:count]


def _iter_policy_rows(pack: Path) -> Iterable[Dict[str, Any]]:
    for path in sorted(pack.glob("dry_run_policy_path_trace_*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def _replay_one(row: Dict[str, Any], backend: Any) -> Dict[str, object]:
    sample_id = str(row["dry_run_sample_id"])
    index = int(sample_id.rsplit("_", 1)[-1])
    kind = POLICY_TO_KIND[str(row["policy"])]
    replay = execute_shadow_profile_request(index, kind, backend, str(row["shadow_profile"]))
    return {
        "dry_run_sample_id": sample_id,
        "policy": row["policy"],
        "expected_stdout": row["expected_stdout"],
        "actual_stdout": replay["actual_stdout"],
        "replay_passed": replay["actual_stdout"] == row["expected_stdout"] and replay["passed"],
        "stdout_mismatch": replay["actual_stdout"] != row["expected_stdout"],
        "source_hash_drift": replay["source_sha256"] != row["source_sha256"],
        "policy_path_drift": replay["builder"] != row["builder"] or replay["emitter"] != row["emitter"],
        "ir_kind_drift": replay["ir_kind"] != row["ir_kind"],
        "compile_failure": not replay["link_invoked"],
        "timeout": bool(replay["timeout"]),
    }


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
