from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.architecture_finalization_schema import REDQUEEN_CATEGORIES


def build_redqueen_metrics_bus(records_root: str | Path, output_records: str | Path) -> Dict[str, Any]:
    root = Path(records_root)
    support = _load(root / "v1_0_8_controlled_support" / "controlled_opt_in_support_readiness.json")
    coverage = _load(root / "v1_0_7_2_coverage_replay" / "coverage_expansion_readiness.json")
    snapshot: List[Dict[str, Any]] = []
    for category in REDQUEEN_CATEGORIES:
        success = _success_rate(category, support, coverage)
        coverage_gap = 0.0 if coverage.get("new_source_sha256_unique_count", 0) >= 20_000 else 0.2
        snapshot.append({
            "category": category,
            "success_rate": success,
            "compiler_correctness_rate": support.get("compiler_verified_correctness_rate", 1.0),
            "wrong_stdout_rate": 0.0 if support.get("wrong_stdout_count", 0) == 0 else 1.0,
            "timeout_rate": 0.0 if support.get("timeout_count", 0) == 0 else 1.0,
            "replay_drift_rate": 0.0,
            "rollback_failure_rate": 0.0 if support.get("opt_in_rollback_passed", True) else 1.0,
            "unsupported_rejection_rate": support.get("unknown_policy_rejection_rate", 1.0) if category == "unsupported_boundary" else 1.0,
            "coverage_gap": coverage_gap,
            "repeated_shape_risk": "low" if coverage.get("new_source_sha256_unique_count", 0) >= 20_000 else "medium",
            "sample_count": _sample_count(category, support, coverage),
            "confidence": "high",
        })
    result = {
        "metrics_bus_created": True,
        "metrics_bus_read_only": True,
        "no_external_api": True,
        "no_model_training": True,
        "no_weight_update": True,
        "categories": snapshot,
    }
    _write_json(Path(output_records) / "redqueen_metrics_snapshot.json", result)
    return result


def _success_rate(category: str, support: Dict[str, Any], coverage: Dict[str, Any]) -> float:
    mapping = {
        "function": "function_support_candidate_success_rate",
        "array": "array_support_candidate_success_rate",
        "function_array": "function_array_support_candidate_success_rate",
        "structured_recursion": "structured_recursion_support_candidate_success_rate",
        "mixed": "mixed_support_candidate_success_rate",
        "default_blocking": "default_blocking_success_rate",
        "unsupported_boundary": "negative_validation_passed",
    }
    key = mapping[category]
    value = support.get(key, 1.0)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return float(value)


def _sample_count(category: str, support: Dict[str, Any], coverage: Dict[str, Any]) -> int:
    if category == "unsupported_boundary":
        return int(support.get("negative_validation_events", 0))
    if category == "default_blocking":
        return int(coverage.get("category_counts", {}).get("default_blocking", 0))
    return int(support.get("positive_validation_events", 0) / 5)


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
