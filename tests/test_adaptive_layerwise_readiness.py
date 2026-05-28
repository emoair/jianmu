from __future__ import annotations

from pathlib import Path

from examples.run_adaptive_layerwise_allocation_balanced_sampling_probe import run_adaptive_layerwise_allocation_balanced_sampling_probe


def test_cross_process_reload_best_profile(tmp_path) -> None:
    result = run_adaptive_layerwise_allocation_balanced_sampling_probe(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12_1",
        "records/v0_9_12",
        tmp_path,
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    assert result["cross"]["cross_process_reload_passed"] is True
    assert result["state"]["best_profile_name"] == "layerwise_sparse_1B_freeze_prune"


def test_integrity_no_forbidden_fields(tmp_path) -> None:
    result = run_adaptive_layerwise_allocation_balanced_sampling_probe(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12_1",
        "records/v0_9_12",
        tmp_path,
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    integrity = result["integrity"]
    assert integrity["forbidden_field_access_count"] == 0
    assert integrity["expected_output_access_before_candidate_generation"] is False
    assert integrity["target_ir_access_before_candidate_generation"] is False


def test_readiness_no_profile_promotion_claim(tmp_path) -> None:
    result = run_adaptive_layerwise_allocation_balanced_sampling_probe(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12_1",
        "records/v0_9_12",
        tmp_path,
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    assert result["state"]["profile_promotion_completed"] is False
    text = (Path(tmp_path) / "mainline_conclusion.json").read_text(encoding="utf-8")
    assert "profile promotion completed" in text


def test_readiness_no_turing_complete_claim(tmp_path) -> None:
    run_adaptive_layerwise_allocation_balanced_sampling_probe(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12_1",
        "records/v0_9_12",
        tmp_path,
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    text = (Path(tmp_path) / "adaptive_layerwise_readiness.json").read_text(encoding="utf-8")
    assert "Turing complete" not in text
    assert "solved program synthesis" not in text


def test_no_expression_oracle_import() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("adaptive_layerwise*.py"))
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("adaptive_layerwise*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("adaptive_layerwise*.py"))
    assert "keyword gate" not in text


def test_real_promotion_disabled(tmp_path) -> None:
    result = run_adaptive_layerwise_allocation_balanced_sampling_probe(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12_1",
        "records/v0_9_12",
        tmp_path,
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    assert result["comparison"]["profile_promotion_completed"] is False
