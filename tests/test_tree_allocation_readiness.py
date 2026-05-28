from __future__ import annotations

from pathlib import Path

from examples.run_access_aware_tree_allocation_dataset_sufficiency_audit import run_access_aware_tree_allocation_dataset_sufficiency_audit


def test_combined_diagnosis_outputs_dominant_cause(tmp_path) -> None:
    result = run_access_aware_tree_allocation_dataset_sufficiency_audit(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12",
        tmp_path,
        ["allocation-audit", "dataset-activation", "resampling-probe", "reallocation-probe", "combined-diagnosis"],
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    assert result["combined"]["dominant_cause"] == "mixed_allocation_and_dataset"
    assert result["readiness"]["recommended_claim_level"] == "mixed_allocation_and_dataset_bottleneck_confirmed"


def test_integrity_no_forbidden_fields(tmp_path) -> None:
    result = run_access_aware_tree_allocation_dataset_sufficiency_audit(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12",
        tmp_path,
        ["allocation-audit"],
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    integrity = result["integrity"]
    assert integrity["forbidden_field_access_count"] == 0
    assert integrity["expected_output_access_before_candidate_generation"] is False
    assert integrity["target_ir_access_before_candidate_generation"] is False


def test_readiness_no_turing_complete_claim(tmp_path) -> None:
    result = run_access_aware_tree_allocation_dataset_sufficiency_audit(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12",
        tmp_path,
        ["allocation-audit"],
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    text = (Path(tmp_path) / "tree_allocation_readiness.json").read_text(encoding="utf-8")
    assert "Turing complete" not in text
    assert result["readiness"]["recommended_claim_level"] != "profile promotion completed"


def test_no_expression_oracle_import() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("*allocation*.py"))
    assert "expression_oracle" not in text


def test_no_external_api_calls() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("*allocation*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_no_hardcoded_keyword_gate() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("*allocation*.py"))
    assert "keyword gate" not in text


def test_real_promotion_disabled(tmp_path) -> None:
    result = run_access_aware_tree_allocation_dataset_sufficiency_audit(
        "datasets/v0_9_9_turing_frontier_curriculum",
        "records/v0_9_12",
        tmp_path,
        ["allocation-audit"],
        samples=20,
        boundary_samples=20,
        run_compiler_validation=False,
        progress=False,
    )
    assert result["combined"]["whether_to_promote_1B_profile"] is False
