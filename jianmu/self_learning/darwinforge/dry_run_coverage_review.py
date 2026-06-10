from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable


def run_dry_run_coverage_review(source_records: str | Path, output_records: str | Path, minimum_unique_compile_units: int = 9000, minimum_source_sha256_unique: int = 9000) -> Dict[str, object]:
    root = Path(source_records)
    pack = root / "dry_run_trace_pack"
    rows = list(_iter_policy_rows(pack))
    policy_distribution = Counter(str(row.get("policy")) for row in rows)
    ir_kind_distribution = Counter(str(row.get("ir_kind")) for row in rows)
    compile_ids = [str(row.get("compile_invocation_id")) for row in rows]
    source_hashes = [str(row.get("source_sha256")) for row in rows]
    total = len(rows)
    expected = {
        "canonical_arithmetic_targetir": "arithmetic_coverage_ok",
        "canonical_function_targetir": "function_coverage_ok",
        "canonical_array_targetir": "array_coverage_ok",
        "canonical_function_array_targetir": "function_array_coverage_ok",
        "canonical_structured_recursion_targetir": "structured_recursion_coverage_ok",
        "mixed_extended_ir_path": "mixed_coverage_ok",
    }
    coverage_flags = {field: policy_distribution.get(policy, 0) > 0 for policy, field in expected.items()}
    max_share = max((count / total for count in policy_distribution.values()), default=0.0)
    trace_shards = sorted(pack.glob("dry_run_policy_path_trace_*.jsonl"))
    notes = []
    if max_share > 0.40:
        notes.append("single_policy_over_40_percent")
    if len(set(source_hashes)) < minimum_source_sha256_unique:
        notes.append("source_sha256_unique_below_threshold")
    duplicate_compile_ids = len(compile_ids) - len(set(compile_ids))
    if duplicate_compile_ids:
        notes.append("duplicate_compile_invocation_id")
    result = {
        "coverage_review_completed": True,
        "total_invocations": total,
        "unique_compile_unit_count": len(set(source_hashes)),
        "policy_distribution": dict(policy_distribution),
        "ir_kind_distribution": dict(ir_kind_distribution),
        "trace_shard_count": len(trace_shards),
        "source_sha256_unique_count": len(set(source_hashes)),
        "compile_invocation_unique_count": len(set(compile_ids)),
        "category_all_represented": all(coverage_flags.values()),
        **coverage_flags,
        "coverage_skew_detected": max_share > 0.40,
        "repeated_shape_risk_level": "low" if len(set(source_hashes)) >= minimum_source_sha256_unique and max_share <= 0.40 else "medium",
        "duplicate_compile_invocation_id_count": duplicate_compile_ids,
        "coverage_review_notes": notes,
    }
    _write_json(Path(output_records) / "dry_run_coverage_review.json", result)
    return result


def _iter_policy_rows(pack: Path) -> Iterable[Dict[str, object]]:
    for path in sorted(pack.glob("dry_run_policy_path_trace_*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
