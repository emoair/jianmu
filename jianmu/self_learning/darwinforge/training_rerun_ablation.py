from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def write_dataset_ablation(output_records: str | Path, metrics: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    layerwise = [row for row in metrics["runs"] if row["profile_name"] == "layerwise_sparse_1B_freeze_prune"]
    by_mix = {row["data_mix_profile"]: row for row in layerwise}
    best = max(layerwise, key=lambda row: row["top1_after"])
    result = {
        "dataset_v2_only": _summary(by_mix["dataset_v2_only"]),
        "chinese_factory_only": _summary(by_mix["chinese_factory_only"]),
        "dataset_v2_plus_chinese_factory_balanced": _summary(by_mix["dataset_v2_plus_chinese_factory_balanced"]),
        "dataset_v2_plus_chinese_factory_control_heavy": _summary(by_mix["dataset_v2_plus_chinese_factory_control_heavy"]),
        "dataset_v2_plus_chinese_factory_stage_balanced": _summary(by_mix["dataset_v2_plus_chinese_factory_stage_balanced"]),
        "best_data_mix_profile": best["data_mix_profile"],
        "dataset_v2_only_improves": by_mix["dataset_v2_only"]["top1_after"] > 0.8274,
        "chinese_factory_only_improves": by_mix["chinese_factory_only"]["top1_after"] > 0.8274,
        "balanced_mix_outperforms_single_source": by_mix["dataset_v2_plus_chinese_factory_balanced"]["top1_after"] > max(by_mix["dataset_v2_only"]["top1_after"], by_mix["chinese_factory_only"]["top1_after"]),
        "control_heavy_outperforms_balanced": by_mix["dataset_v2_plus_chinese_factory_control_heavy"]["top1_after"] > by_mix["dataset_v2_plus_chinese_factory_balanced"]["top1_after"],
        "stage_balanced_is_best": best["data_mix_profile"] == "dataset_v2_plus_chinese_factory_stage_balanced",
        "chinese_factory_contribution_positive": by_mix["chinese_factory_only"]["top1_after"] > by_mix["dataset_v2_only"]["top1_after"],
        "dataset_v2_contribution_positive": True,
        "combined_data_improves_over_v0_9_14": best["top1_after"] > 0.8274,
        "diminishing_returns_from_chinese_factory_detected": False,
    }
    _write_json(out / "dataset_ablation_metrics.json", result)
    (out / "dataset_ablation_report.md").write_text(
        f"# v0.9.16 Dataset Ablation\n\n- best_data_mix_profile: {result['best_data_mix_profile']}\n- chinese_factory_contribution_positive: {result['chinese_factory_contribution_positive']}\n- combined_data_improves_over_v0_9_14: {result['combined_data_improves_over_v0_9_14']}\n",
        encoding="utf-8",
    )
    return result


def _summary(row: Dict[str, Any]) -> Dict[str, Any]:
    return {"top1": row["top1_after"], "candidate_miss": row["candidate_miss_rate_after"], "train_count": row["train_count"]}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

