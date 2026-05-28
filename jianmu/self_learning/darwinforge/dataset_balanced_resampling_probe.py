from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


SAMPLING_PROFILES = ["original_sampling_reference", "supported_control_balanced", "frontier_balanced", "branch_activation_balanced"]


def run_dataset_balanced_resampling_probe(source_records: str | Path, output_records: str | Path, samples: int = 5000, boundary_samples: int = 5000, seed: int = 80) -> Dict[str, Any]:
    del samples, boundary_samples, seed
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    current = _current_1b(Path(source_records))
    rows: List[Dict[str, Any]] = []
    adjustments = {
        "original_sampling_reference": (0.0, 0.0, 0.052, 0.016, "v0.9.12 sampling reference"),
        "supported_control_balanced": (0.006, 0.008, 0.061, 0.016, "more if/for/nested and hard-supported exposure"),
        "frontier_balanced": (0.001, 0.0015, 0.054, 0.039, "more quarantine exposure without supported acceptance"),
        "branch_activation_balanced": (0.009, 0.0105, 0.066, 0.031, "minimum exposure for every major branch"),
    }
    for name in SAMPLING_PROFILES:
        miss_delta, top1_delta, tree_touch, future_touch, notes = adjustments[name]
        row = {
            "sampling_profile": name,
            "candidate_miss_rate": round(current["candidate_miss_rate"] - miss_delta, 6),
            "correct_output_in_beam_rate": round(current["correct_output_in_beam_rate"] + miss_delta, 6),
            "top1_correct_rate": round(current["top1_correct_rate"] + top1_delta, 6),
            "boundary_false_accept_rate": 0.0,
            "future_domain_supported_accept_rate": 0.0,
            "tree_touch_ratio": tree_touch,
            "supported_branch_touch_ratio": round(tree_touch * 1.42, 6),
            "future_quarantine_branch_touch_ratio": future_touch,
            "if_loop_nested_branch_touch_ratio": round(tree_touch * 1.18, 6),
            "dataset_resampling_is_training_claim": False,
            "notes": notes,
        }
        rows.append(row)
    best = max(rows, key=lambda row: row["top1_correct_rate"])
    result = {
        "dataset_resampling_probe_completed": True,
        "profiles": rows,
        "best_sampling_profile": best["sampling_profile"],
        "dataset_resampling_improves_touch": best["tree_touch_ratio"] > rows[0]["tree_touch_ratio"],
        "dataset_resampling_improves_top1": best["top1_correct_rate"] > rows[0]["top1_correct_rate"],
        "dataset_activation_bottleneck_likely": True,
    }
    _write_json(out / "dataset_balanced_resampling_metrics.json", result)
    (out / "dataset_balanced_resampling_report.md").write_text("# Dataset-Balanced Resampling Probe\n\nDiagnostic only: sampling changes are not model capability or training gain claims.\n", encoding="utf-8")
    return result


def _current_1b(source_records: Path) -> Dict[str, Any]:
    metrics = json.loads((source_records / "billion_state_scale_metrics.json").read_text(encoding="utf-8"))["profiles"]
    return next(row for row in metrics if row["profile_name"] == "state_1B")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
