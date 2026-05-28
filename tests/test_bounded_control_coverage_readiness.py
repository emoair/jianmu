from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.bounded_control_coverage_readiness import load_coverage_readiness


def test_readiness_no_turing_complete_claim(tmp_path) -> None:
    path = tmp_path / "readiness.json"
    path.write_text(json.dumps({"recommended_claim_level": "turing_frontier_dataset_ready_budget_probe_mixed"}), encoding="utf-8")
    assert load_coverage_readiness(path)["recommended_claim_level"].endswith("mixed")


def test_no_expression_oracle_import() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_control_candidate_space_probe.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = Path("jianmu/self_learning/darwinforge/turing_frontier_generator.py").read_text(encoding="utf-8").lower()
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = Path("jianmu/self_learning/darwinforge/bounded_control_candidate_space_probe.py").read_text(encoding="utf-8").lower()
    assert "keyword gate" not in text


def test_real_promotion_disabled() -> None:
    text = Path("docs/experiments/TURING_FRONTIER_DATASET_CANDIDATE_SPACE_SCALE_PROBE.md").read_text(encoding="utf-8").lower()
    assert "safe real promotion" in text

