from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


HISTORY = {
    "v0.9.7": 0.3866,
    "v0.9.8": 0.3818,
    "v0.9.10": 0.7096,
    "v0.9.11": 0.76864,
    "v0.9.12": 0.78768,
    "v0.9.13": 0.8274,
    "v0.9.14": 0.8274,
}


def write_training_rerun_historical_regression(output_records: str | Path, best_top1: float, best_candidate_miss: float) -> Dict[str, Any]:
    out = Path(output_records)
    result = {
        "history_top1": HISTORY,
        "v0_9_16_best_top1": best_top1,
        "v0_9_16_best_candidate_miss": best_candidate_miss,
        "comparable_scope": "supported bounded-control Chinese current-supported",
        "arithmetic_1_0_not_directly_comparable": True,
        "future_function_array_recursion_not_supported": True,
        "regressed_vs_v0_9_14": best_top1 < HISTORY["v0.9.14"],
        "improved_vs_v0_9_14": best_top1 > HISTORY["v0.9.14"],
        "improved_vs_v0_9_13": best_top1 > HISTORY["v0.9.13"],
        "improved_vs_v0_9_10": best_top1 > HISTORY["v0.9.10"],
        "historical_regression_gate_passed": best_top1 >= HISTORY["v0.9.14"],
    }
    _write_json(out / "historical_regression.json", result)
    (out / "historical_regression.md").write_text(
        f"# v0.9.16 Historical Regression\n\n- best_top1: {best_top1}\n- best_candidate_miss: {best_candidate_miss}\n- historical_regression_gate_passed: {result['historical_regression_gate_passed']}\n- future function/array/recursion remain not supported.\n",
        encoding="utf-8",
    )
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

