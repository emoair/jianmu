from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def assess_plateau_readiness(
    progress: Dict[str, Any],
    taxonomy: Dict[str, Any],
    beam: Dict[str, Any],
    ablation: Dict[str, Any],
    stage: Dict[str, Any],
    integrity: Dict[str, Any],
    output_records: str | Path | None = None,
) -> Dict[str, Any]:
    blocking: List[str] = []
    if progress.get("progress_events_emitted", 0) < 20:
        blocking.append("progress_event_count_low")
    if not progress.get("progress_metrics_safe"):
        blocking.append("progress_metrics_not_safe")
    if not taxonomy.get("candidate_error_taxonomy_completed"):
        blocking.append("candidate_taxonomy_missing")
    if not beam.get("beam_sweep_completed"):
        blocking.append("beam_sweep_missing")
    if not ablation.get("ablation_diagnosis_completed"):
        blocking.append("ablation_diagnosis_missing")
    if not stage.get("stage_plateau_diagnosis_completed"):
        blocking.append("stage_diagnosis_missing")
    if not integrity.get("integrity_check_passed"):
        blocking.append("integrity_check_failed")
    candidate_miss = taxonomy.get("candidate_miss_rate", 0.0)
    wrong_top1 = taxonomy.get("in_beam_wrong_top1_rate", 0.0)
    if candidate_miss >= wrong_top1 and candidate_miss >= 0.3:
        dominant = "candidate_miss_generation_bottleneck"
        next_action = "diagnose candidate generation/search-space coverage for bounded control stages"
    elif beam.get("ranking_bottleneck_likely"):
        dominant = "ranking_or_scorer_bottleneck"
        next_action = "diagnose scorer/router ordering on in-beam correct candidates"
    else:
        dominant = "mixed_stage_and_ablation_bottleneck"
        next_action = "run targeted stage diagnostics on weakest bounded control stages"
    claim = "progress_repaired_plateau_diagnosed" if not blocking else "progress_repaired_plateau_partially_diagnosed"
    if "progress_event_count_low" in blocking:
        claim = "progress_not_fixed"
    if "integrity_check_failed" in blocking:
        claim = "diagnosis_failed"
    result = {
        "progress_repair_completed": "progress_event_count_low" not in blocking,
        "progress_events_emitted": progress.get("progress_events_emitted", 0),
        "progress_metrics_safe": progress.get("progress_metrics_safe", False),
        "plateau_diagnosis_completed": not any(item in blocking for item in ["candidate_taxonomy_missing", "beam_sweep_missing", "ablation_diagnosis_missing", "stage_diagnosis_missing"]),
        "candidate_error_taxonomy_completed": taxonomy.get("candidate_error_taxonomy_completed", False),
        "beam_sweep_completed": beam.get("beam_sweep_completed", False),
        "ablation_diagnosis_completed": ablation.get("ablation_diagnosis_completed", False),
        "stage_plateau_diagnosis_completed": stage.get("stage_plateau_diagnosis_completed", False),
        "dominant_plateau_cause": dominant,
        "candidate_miss_rate": candidate_miss,
        "in_beam_wrong_top1_rate": wrong_top1,
        "beam_bottleneck_likely": beam.get("beam_bottleneck_likely", False),
        "ranking_bottleneck_likely": beam.get("ranking_bottleneck_likely", False),
        "generation_bottleneck_likely": beam.get("generation_bottleneck_likely", False),
        "root_colony_gain_present": ablation.get("root_colony_gain_present", False),
        "nutrient_toxic_gain_present": ablation.get("nutrient_toxic_gain_present", False),
        "lifecycle_gain_present": ablation.get("lifecycle_gain_present", False),
        "recommended_next_action": next_action,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "targeted bounded-substrate candidate-space diagnosis; do not claim stronger model capability from diagnostics",
    }
    if output_records:
        Path(output_records).mkdir(parents=True, exist_ok=True)
        (Path(output_records) / "plateau_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

