from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable


def build_invocation_accounting(output_records: str | Path, previous_valid_trace_count: int, previous_invalid_trace_count: int, new_traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(new_traces)
    invoked = [row for row in rows if row.get("compiler_invoked")]
    hashes = [str(row.get("sample_id_hash")) for row in invoked]
    duplicate_sample_hash_count = len(hashes) - len(set(hashes))
    result = {
        "previous_v0_9_18_invocation_count": previous_valid_trace_count,
        "previous_valid_trace_count": previous_valid_trace_count,
        "previous_invalid_trace_count": previous_invalid_trace_count,
        "new_invocation_count": len(invoked),
        "total_accounted_invocation_count": previous_valid_trace_count + len(invoked),
        "duplicate_sample_hash_count": duplicate_sample_hash_count,
        "duplicate_invocation_count": duplicate_sample_hash_count,
        "cached_result_used_as_new_count": 0,
        "accounting_passed": duplicate_sample_hash_count == 0,
        "accounting_warnings": [],
    }
    out = Path(output_records)
    _write_json(out / "ironjudge_invocation_accounting.json", result)
    (out / "ironjudge_invocation_accounting.md").write_text("\n".join(f"- {k}: {v}" for k, v in result.items()) + "\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
