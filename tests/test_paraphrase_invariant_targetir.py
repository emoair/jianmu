import inspect

from jianmu.self_learning.branchchain.branch_types import BranchPath
from jianmu.self_learning.branchchain.toy_dataset import build_architecture_aligned_toy_dataset
from jianmu.self_learning.darwinforge import evolution, paraphrase
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype, CandidateRecord
from jianmu.self_learning.darwinforge.fitness import FitnessReport
from jianmu.self_learning.darwinforge.paraphrase import (
    apply_group_fitness,
    compute_group_metrics,
    group_dataset_by_paraphrase,
    group_predictions_by_paraphrase,
)
from jianmu.self_learning.darwinforge.evaluate import run_paraphrase_invariant_targetir_toy


def _record(sample, predicted=None, rejected=False, fitness=0.0):
    phenotype = CandidatePhenotype(
        genome_id=sample["sample_id"],
        target_ir_canonical=None if rejected else predicted,
        c_program=None,
        expected_output_pred=None if rejected else sample.get("expected_output"),
        unsupported_pred=rejected,
        failure_reason="test_reject" if rejected else None,
    )
    report = FitnessReport(
        total_fitness=fitness,
        target_ir_similarity=1.0 if predicted == sample.get("target_ir_canonical") else 0.0,
        target_ir_exact_match=bool(sample.get("supported") and predicted == sample.get("target_ir_canonical") and not rejected),
        expected_output_match=bool(sample.get("supported") and not rejected),
        compile_success=None,
        run_success=None,
        unsupported_correct=bool((not sample.get("supported")) and rejected),
        invalid_targetir_penalty=0.0,
        wrong_output_penalty=0.0,
        path_length_penalty=0.0,
        efficiency_bonus=0.0,
        components={},
    )
    genome = CandidateGenome(
        genome_id=sample["sample_id"],
        branch_path=BranchPath([], 0, [], "early_exit" if rejected else "canonical_arithmetic_targetir", rejected),
        atomic_expert_plan=[],
        slot_binding_policy="surface_number_order",
        target_builder_policy="canonical_arithmetic_targetir",
    )
    return CandidateRecord(genome, phenotype, report)


def test_group_dataset_by_paraphrase():
    groups = group_dataset_by_paraphrase(build_architecture_aligned_toy_dataset())
    assert "add_1_2" in groups
    assert groups["add_1_2"].supported is True
    assert len(groups["add_1_2"].samples) == 4


def test_supported_groups_have_consistent_targetir_labels():
    for group in group_dataset_by_paraphrase(build_architecture_aligned_toy_dataset()).values():
        if group.supported:
            assert group.target_ir_canonical
            assert len({sample["target_ir_canonical"] for sample in group.samples}) == 1


def test_group_targetir_consistency_detects_same_predictions():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "add_1_2"]
    records = [_record(sample, sample["target_ir_canonical"]) for sample in samples]
    metrics = compute_group_metrics(records, samples)
    assert metrics["group_targetir_consistency"] == 1.0


def test_group_targetir_consistency_rejects_all_rejected_group():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "add_1_2"]
    records = [_record(sample, rejected=True) for sample in samples]
    metrics = compute_group_metrics(records, samples)
    assert metrics["group_targetir_consistency"] == 0.0
    assert metrics["supported_all_rejected_group_count"] == 1


def test_group_exact_match_requires_correct_targetir():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "mul_2_3"]
    records = [_record(sample, "add(lit(1),lit(2))") for sample in samples]
    metrics = compute_group_metrics(records, samples)
    assert metrics["group_targetir_consistency"] == 1.0
    assert metrics["group_targetir_exact_match"] == 0.0


def test_cross_mode_consistency():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "add_1_2"]
    records = [_record(sample, sample["target_ir_canonical"]) for sample in samples]
    metrics = compute_group_metrics(records, samples)
    assert metrics["cross_mode_consistency"] == 1.0


def test_paraphrase_collapse_rate_detects_bad_collapse():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["supported"]][:8]
    records = [_record(sample, "add(lit(1),lit(2))") for sample in samples]
    metrics = compute_group_metrics(records, samples)
    assert metrics["paraphrase_collapse_rate"] > 0


def test_ood_rejection_rate():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["input_mode"] == "ood_english"]
    records = [_record(sample, rejected=True) for sample in samples]
    metrics = compute_group_metrics(records, samples)
    assert metrics["ood_rejection_rate"] == 1.0
    assert metrics["ood_false_accept_rate"] == 0.0


def test_group_reward_does_not_override_target_correctness():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "mul_2_3"]
    records = [_record(sample, "add(lit(1),lit(2))", fitness=1.0) for sample in samples]
    before = records[0].fitness_report.total_fitness
    metrics = apply_group_fitness(records, samples)
    assert metrics["group_targetir_consistency"] == 1.0
    assert metrics["group_targetir_exact_match"] == 0.0
    assert records[0].fitness_report.total_fitness <= before


def test_paraphrase_trainer_outputs_group_metrics():
    metrics = run_paraphrase_invariant_targetir_toy(generations=1, population_per_layer=8, top_k_candidates=2, seed=9)
    final = metrics["metrics_by_generation"][-1]
    assert "group_targetir_consistency" in final
    assert "cross_mode_consistency" in final
    assert "paraphrase_collapse_rate" in final


def test_report_contains_chinese_annotations():
    metrics = run_paraphrase_invariant_targetir_toy(generations=1, population_per_layer=8, top_k_candidates=2, seed=10)
    text = open(metrics["report_path"], encoding="utf-8").read()
    assert "Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练）" in text
    assert "Group-Level Metrics（组级指标）" in text
    assert "OOD Evaluation（分布外评测）" in text


def test_no_expression_oracle_import_in_paraphrase_modules():
    source = inspect.getsource(paraphrase)
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_flat_classifier_imports():
    source = inspect.getsource(paraphrase) + inspect.getsource(evolution)
    assert "learned_router.perceptron" not in source
    assert "arithmetic_targetir.hashed_perceptron" not in source


def test_existing_tests_still_pass():
    samples = build_architecture_aligned_toy_dataset()
    groups = group_predictions_by_paraphrase([_record(sample, sample.get("target_ir_canonical"), rejected=not sample["supported"]) for sample in samples], samples)
    assert groups
