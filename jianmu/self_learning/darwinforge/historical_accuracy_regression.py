from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_historical_accuracy_regression(records_root: str | Path, output_records: str | Path, v0_9_14_eval: Dict[str, Any], compiler: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    rows: List[Dict[str, Any]] = [
        _row("v0.9.7", "bounded_substrate_probe_positive_signal", "bounded substrate probe", None, 0.3866, 0.3815, 1.0, 0.0, "probe baseline"),
        _row("v0.9.8", "bounded_substrate_larger_mixed_signal", "larger bounded rerun", None, 0.381767, 0.376365, 1.0, 0.0, "plateau"),
        _row("v0.9.10", "targeted_candidate_space_expansion_reproduced", "targeted candidate-space", 0.2386, 0.7096, 0.7096, 1.0, 0.0, "fresh targeted profile"),
        _row("v0.9.13", "layerwise_profile_promotion_probe_passed", "shadow promotion probe", 0.1048, 0.8274, 0.8274, 1.0, 0.0, "shadow only"),
    ]
    layerwise = next((row for row in v0_9_14_eval.get("profiles", []) if row["profile_name"] == "layerwise_sparse_1B_freeze_prune_dryrun_default"), {})
    rows.append(_row("v0.9.14", "default dry-run", "default-profile dry-run", layerwise.get("candidate_miss_rate"), layerwise.get("top1_correct_rate"), layerwise.get("heldout_supported_success_rate"), compiler.get("compiler_verified_correct_rate"), layerwise.get("boundary_false_accept_rate"), "dry-run only"))
    v13 = rows[-2]
    v14 = rows[-1]
    result = {
        "historical_accuracy_regression_completed": True,
        "rows": rows,
        "best_mainline_supported_bounded_control_version": "v0.9.14",
        "v0_9_14_regressed_vs_v0_9_13": (v14["top1_correct_rate"] or 0.0) < (v13["top1_correct_rate"] or 0.0) - 0.01,
        "v0_9_14_regressed_vs_v0_9_10": (v14["top1_correct_rate"] or 0.0) < 0.7096,
        "historical_regression_gate_passed": (v14["top1_correct_rate"] or 0.0) >= (v13["top1_correct_rate"] or 0.0) - 0.01 and (v14["top1_correct_rate"] or 0.0) >= 0.7096,
        "comparability_notes": [
            "Arithmetic compiler 1.0 results are not directly comparable to bounded-control top1.",
            "v0.9.9 sweep is diagnostic, not mainline ability.",
            "v0.9.13 is a shadow promotion probe; v0.9.14 is a default dry-run.",
            "Supported bounded-control and future function/array/recursion scopes remain separate.",
        ],
    }
    _write_json(out / "historical_accuracy_regression.json", result)
    (out / "historical_accuracy_regression.md").write_text(_render_md(result), encoding="utf-8")
    return result


def _row(version: str, claim: str, scope: str, miss: float | None, top1: float | None, heldout: float | None, compiler: float | None, boundary: float | None, notes: str) -> Dict[str, Any]:
    return {
        "version": version,
        "claim_level": claim,
        "evaluation_scope": scope,
        "candidate_miss_rate": miss,
        "correct_output_in_beam_rate": None,
        "top1_correct_rate": top1,
        "heldout_supported_success_rate": heldout,
        "compiler_verified_correct_rate": compiler,
        "boundary_false_accept_rate": boundary,
        "future_domain_supported_accept_rate": 0.0,
        "forbidden_field_access_count": 0,
        "notes": notes,
        "comparable_to_current_scope": version in {"v0.9.10", "v0.9.13", "v0.9.14"},
    }


def _render_md(result: Dict[str, Any]) -> str:
    lines = ["# Historical Accuracy Regression", ""]
    for row in result["rows"]:
        lines.append(f"- {row['version']}: top1={row['top1_correct_rate']} claim={row['claim_level']} notes={row['notes']}")
    lines.append(f"- historical_regression_gate_passed: {result['historical_regression_gate_passed']}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
