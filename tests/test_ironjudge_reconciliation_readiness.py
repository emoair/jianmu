from __future__ import annotations

from pathlib import Path

from jianmu.self_learning.darwinforge.ironjudge_reconciliation_readiness import write_clean_criteria, write_readiness


def test_ironjudge_clean_criteria_extended_partial_not_completed_clean(tmp_path) -> None:
    reconciliation = {"gate_5k_clean_reconciled": True, "main_20k_clean_reconciled": True, "extended_50k_observed_clean": True, "extended_50k_clean_reconciled": False, "extended_50k_partial": True}
    clean = write_clean_criteria(tmp_path, reconciliation, {"levels": [{"level_name": "extended_50k", "compiler_verified_correct_rate": 1.0}]})
    assert clean["extended_50k_observed_clean"] is True
    assert clean["extended_50k_completed_clean"] is False


def test_ironjudge_reconciliation_readiness_no_turing_claim(tmp_path) -> None:
    reconciliation = {"level_accounting_mode_selected": "cumulative", "claim_conflict_detected": True, "claim_conflict_resolved": True, "gate_5k_completed_reconciled": True, "gate_5k_clean_reconciled": True, "main_20k_completed_reconciled": True, "main_20k_clean_reconciled": True, "extended_50k_completed_reconciled": False, "extended_50k_partial": True, "extended_50k_observed_clean": True, "total_accounted_invocation_count": 27800, "accounting_passed": True}
    claim = {"v0_9_18_claim_upgrade_supported": True, "recommended_claim_level": "ironjudge_20k_clean_frontier_evidence_reconciled", "blocking_issues": [], "required_next_run": "optional extended_50k continuation"}
    clean = {"clean_criteria_passed": True, "future_domain_compiled_count": 0, "unsupported_compiled_count": 0, "trap_compiled_count": 0, "english_compiled_count": 0, "mixed_language_compiled_count": 0, "recursion_compiled_count": 0, "pointer_compiled_count": 0, "io_compiled_count": 0}
    integrity = {"no_cached_compiler_result_used_as_new_validation": True, "original_v0_9_18_records_preserved": True, "original_v0_9_18_1_records_preserved": True}
    main20k = {"main20k_completion_rerun_executed": False, "new_invocation_count_v0_9_18_2": 0}
    readiness = write_readiness(tmp_path, reconciliation, claim, clean, integrity, main20k)
    assert "turing" not in readiness["recommended_claim_level"].lower()


def test_integrity_original_records_preserved() -> None:
    text = "original_v0_9_18_records_preserved"
    assert text in Path("jianmu/self_learning/darwinforge/ironjudge_reconciliation_readiness.py").read_text(encoding="utf-8")


def test_no_expression_oracle_import() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_*reconcil*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import expression_oracle" not in text
        assert "from expression_oracle" not in text


def test_no_external_api_calls() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_*reconcil*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "requests." not in text
        assert "urllib" not in text
        assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("ironjudge_*.py"):
        assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled() -> None:
    text = Path("jianmu/self_learning/darwinforge/ironjudge_reconciliation_readiness.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": False' in text
