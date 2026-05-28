from __future__ import annotations

import json

from jianmu.self_learning.darwinforge.bounded_substrate_plateau_diagnosis import run_ablation_plateau_diagnosis, run_integrity_check, run_stage_plateau_diagnosis


def test_plateau_ablation_diagnosis_outputs_deltas(tmp_path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "bounded_substrate_baseline_ablation.json").write_text(json.dumps({"baseline_gap_verified": True, "variants": {"full_jianmu_bounded_substrate": {"top1_correct_rate": 0.4}, "no_root_colony": {"top1_correct_rate": 0.2, "executed": True}}}), encoding="utf-8")
    result = run_ablation_plateau_diagnosis(src, tmp_path / "out")
    assert result["variants"]["no_root_colony"]["delta_vs_full"] == -0.2


def test_stage_plateau_diagnosis_compares_v0_9_7_and_v0_9_8(tmp_path) -> None:
    src = tmp_path / "src"
    base = tmp_path / "base"
    src.mkdir()
    base.mkdir()
    stage_payload = {"by_stage": {"variable_declaration": {"top1_correct_after": 0.4, "candidate_hit_after": 0.4, "correct_output_in_beam_after": 0.4}}}
    base_payload = {"by_stage": {"variable_declaration": {"top1_correct_after": 0.3, "candidate_hit_after": 0.3, "correct_output_in_beam_after": 0.3}}}
    (src / "bounded_substrate_larger_stage_metrics.json").write_text(json.dumps(stage_payload), encoding="utf-8")
    (base / "bounded_substrate_stage_metrics.json").write_text(json.dumps(base_payload), encoding="utf-8")
    result = run_stage_plateau_diagnosis(src, base, tmp_path / "out")
    assert "variable_declaration" in result["stages_improved"]


def test_integrity_check_blocks_fixed_summary_periodic(tmp_path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "bounded_substrate_larger_training_metrics.json").write_text(json.dumps({"fixed_metric_detected": True, "mandatory_counter_guard_passed": True}), encoding="utf-8")
    (src / "sample_processing_counters.json").write_text(json.dumps({"mandatory_counter_guard_passed": True}), encoding="utf-8")
    result = run_integrity_check(src, tmp_path / "out")
    assert result["integrity_check_passed"] is False

