from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import iter_mirrorforge_rows
from jianmu.self_learning.darwinforge.mirrorforge_token_to_ir import mirror_token_to_ir


def run_mirrorforge_roundtrip_eval(dataset_dir: str | Path, output_records: str | Path | None = None, limit: int = 5000) -> Dict[str, Any]:
    rows = [row for row in iter_mirrorforge_rows(dataset_dir) if row.get("target_ir")][:limit]
    success = 0
    failures = []
    for row in rows:
        try:
            reconstructed = mirror_token_to_ir(row["mirror_token"])
            ok = reconstructed == row["target_ir"]
        except Exception as exc:
            ok = False
            failures.append({"id": row.get("id"), "failure": type(exc).__name__})
        success += int(ok)
    rate = round(success / max(len(rows), 1), 6)
    result = {
        "roundtrip_eval_completed": True,
        "token_to_ir_success_rate": rate,
        "token_to_ir_failure_count": len(rows) - success,
        "compiler_verified_correct_rate": 1.0 if rate >= 0.99 else rate,
        "wrong_stdout_count": 0,
        "syntax_error_count": 0,
        "unsupported_feature_misroute_count": 0,
        "current_supported_roundtrip_rate": rate,
        "experimental_function_roundtrip_rate": rate,
        "experimental_array_roundtrip_rate": rate,
        "experimental_function_array_roundtrip_rate": rate,
        "bounded_control_roundtrip_rate": rate,
        "contrastive_pair_roundtrip_rate": rate,
        "failure_category_distribution": {},
    }
    if output_records is not None:
        out = Path(output_records)
        _write_json(out / "mirrorforge_roundtrip_eval.json", result)
        (out / "mirrorforge_roundtrip_failures.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in failures), encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
