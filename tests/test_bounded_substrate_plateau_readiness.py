from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.bounded_substrate_plateau_readiness import assess_plateau_readiness


def test_plateau_readiness_no_turing_complete_claim(tmp_path) -> None:
    readiness = assess_plateau_readiness(
        {"progress_events_emitted": 25, "progress_metrics_safe": True},
        {"candidate_error_taxonomy_completed": True, "candidate_miss_rate": 0.5, "in_beam_wrong_top1_rate": 0.0},
        {"beam_sweep_completed": True, "generation_bottleneck_likely": True},
        {"ablation_diagnosis_completed": True},
        {"stage_plateau_diagnosis_completed": True},
        {"integrity_check_passed": True},
        tmp_path,
    )
    assert readiness["recommended_claim_level"] == "progress_repaired_plateau_diagnosed"
    assert "Turing" not in readiness["recommended_claim_level"]


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_substrate_plateau_readiness.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_substrate_plateau_diagnosis.py").read_text(encoding="utf-8").lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_substrate_plateau_diagnosis.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    text = Path("docs/experiments/PROGRESS_REPAIR_PLATEAU_DIAGNOSIS.md").read_text(encoding="utf-8").lower()
    assert "safe real promotion" in text

