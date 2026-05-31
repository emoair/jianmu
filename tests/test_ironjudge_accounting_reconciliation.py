from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.ironjudge_accounting_reconciliation import build_accounting_reconciliation


def _records(tmp_path: Path) -> tuple[Path, Path]:
    v18 = tmp_path / "v18"
    v181 = tmp_path / "v181"
    v18.mkdir()
    v181.mkdir()
    (v181 / "ironjudge_resumable_scaleup.json").write_text(json.dumps({"levels": [{"level_name": "gate_5k", "completed_invocations": 5000, "previous_invocations_used": 2848, "compiler_verified_correct_rate": 1.0, "wrong_stdout_count": 0}, {"level_name": "main_20k", "completed_invocations": 16440, "previous_invocations_used": 5000, "compiler_verified_correct_rate": 1.0, "wrong_stdout_count": 0}, {"level_name": "extended_50k", "completed_invocations": 27800, "previous_invocations_used": 16440, "partial": True, "compiler_verified_correct_rate": 1.0, "wrong_stdout_count": 0}]}), encoding="utf-8")
    (v181 / "ironjudge_invocation_accounting.json").write_text(json.dumps({"previous_v0_9_18_invocation_count": 2848, "new_invocation_count": 24952, "total_accounted_invocation_count": 27800, "accounting_passed": True}), encoding="utf-8")
    (v181 / "ironjudge_scaleup_readiness.json").write_text(json.dumps({"main_20k_completed": False, "recommended_claim_level": "ironjudge_20k_clean_frontier_evidence_strengthened"}), encoding="utf-8")
    return v18, v181


def test_ironjudge_accounting_reconciliation_detects_conflict(tmp_path: Path) -> None:
    v18, v181 = _records(tmp_path)
    result = build_accounting_reconciliation(v18, v181, tmp_path / "out")
    assert result["claim_conflict_detected"] is True
    assert result["claim_conflict_resolved"] is True
    assert result["main_20k_completed_reconciled"] is True
