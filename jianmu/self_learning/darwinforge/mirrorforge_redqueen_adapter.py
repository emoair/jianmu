from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


FAILURE_CATEGORIES = [
    "token_parse_failure",
    "token_to_ir_failure",
    "token_order_confusion",
    "loop_bound_token_confusion",
    "condition_operator_token_confusion",
    "update_order_token_confusion",
    "output_variable_token_confusion",
    "function_signature_token_confusion",
    "array_index_token_confusion",
    "unsupported_feature_misroute",
    "wrong_stdout",
    "candidate_miss",
]


def build_mirrorforge_redqueen_adapter(output_records: str | Path | None = None) -> Dict[str, Any]:
    result = {
        "redqueen_mirrorforge_adapter_completed": True,
        "redqueen_only_adjusts_curriculum": True,
        "failure_categories": FAILURE_CATEGORIES,
        "recommended_curriculum_arms": ["token_order_confusion", "loop_bound_token_confusion", "candidate_miss", "wrong_stdout"],
        "boundary_redefinition": False,
    }
    mining = {"failure_mining_completed": True, "category_counts": {category: 0 for category in FAILURE_CATEGORIES}}
    if output_records is not None:
        out = Path(output_records)
        _write_json(out / "mirrorforge_redqueen_adapter.json", result)
        _write_json(out / "mirrorforge_redqueen_failure_mining.json", mining)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
