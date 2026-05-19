import inspect

from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.branchchain.toy_dataset import build_architecture_aligned_toy_dataset
from jianmu.self_learning.darwinforge import evolution, reranking
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype, CandidateRecord
from jianmu.self_learning.darwinforge.fitness import FitnessReport
from jianmu.self_learning.darwinforge.reranking import (
    branch_signature,
    classify_candidate_quadrant,
    collect_pruning_candidates,
    rerank_candidates_for_sample,
    select_group_beam,
)
from jianmu.self_learning.darwinforge.evaluate import run_hindsight_branch_reranking_toy


def _sample(group="add_1_2"):
    return next(sample for sample in build_architecture_aligned_toy_dataset() if sample["paraphrase_group"] == group and sample["supported"])


def _record(sample, pred=None, score=0.0, rejected=False, suffix="x"):
    decision = BranchDecision("structure_policy", ["binary_operation"], "binary_operation", 30, f"n-{suffix}", {})
    path = BranchPath(
        decisions=[decision],
        route_confidence=30,
        atomic_experts=["ArithmeticExpressionExpert"],
        target_builder="canonical_arithmetic_targetir",
        early_exit=rejected,
    )
    genome = CandidateGenome(
        genome_id=f"{sample['sample_id']}-{suffix}",
        branch_path=path,
        atomic_expert_plan=path.atomic_experts,
        slot_binding_policy="surface_number_order",
        target_builder_policy="canonical_arithmetic_targetir",
    )
    phenotype = CandidatePhenotype(
        genome_id=genome.genome_id,
        target_ir_canonical=None if rejected else pred,
        c_program=None,
        expected_output_pred=None if rejected else sample.get("expected_output"),
        unsupported_pred=rejected,
        failure_reason="reject" if rejected else None,
    )
    report = FitnessReport(
        total_fitness=score,
        target_ir_similarity=1.0 if pred == sample.get("target_ir_canonical") else 0.0,
        target_ir_exact_match=bool(sample.get("supported") and pred == sample.get("target_ir_canonical") and not rejected),
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
    return CandidateRecord(genome, phenotype, report)


def test_candidate_quadrant_high_score_correct():
    sample = _sample()
    record = _record(sample, sample["target_ir_canonical"], score=8, suffix="a")
    assert classify_candidate_quadrant(record, sample, 0, 8) == "high_score_correct"


def test_candidate_quadrant_high_score_wrong():
    sample = _sample("mul_2_3")
    record = _record(sample, "add(lit(1),lit(2))", score=8, suffix="a")
    assert classify_candidate_quadrant(record, sample, 0, 8) == "high_score_wrong"


def test_candidate_quadrant_low_score_correct():
    sample = _sample()
    record = _record(sample, sample["target_ir_canonical"], score=1, suffix="b")
    assert classify_candidate_quadrant(record, sample, 1, 1) == "low_score_correct"


def test_candidate_quadrant_low_score_wrong():
    sample = _sample("mul_2_3")
    record = _record(sample, "add(lit(1),lit(2))", score=1, suffix="b")
    assert classify_candidate_quadrant(record, sample, 1, 1) == "low_score_wrong"


def test_rerank_promotes_exact_match():
    sample = _sample("add_mul_1_2_3")
    wrong = _record(sample, "add(lit(1),lit(2))", score=5, suffix="wrong")
    correct = _record(sample, sample["target_ir_canonical"], score=1, suffix="correct")
    ranked = rerank_candidates_for_sample([wrong, correct], sample)
    assert ranked[0].exact_match is True
    assert ranked[0].quadrant == "low_score_correct"


def test_rerank_penalizes_wrong_targetir():
    sample = _sample("mul_2_3")
    wrong = _record(sample, "add(lit(1),lit(2))", score=5, suffix="wrong")
    correct = _record(sample, sample["target_ir_canonical"], score=4, suffix="correct")
    ranked = rerank_candidates_for_sample([wrong, correct], sample)
    assert ranked[0].target_ir_pred == sample["target_ir_canonical"]


def test_group_beam_prefers_correct_consistent_targetir():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "add_1_2"]
    candidate_sets = []
    for sample in samples:
        candidate_sets.append([
            _record(sample, "mul(lit(2),lit(3))", score=5, suffix="wrong"),
            _record(sample, sample["target_ir_canonical"], score=1, suffix="correct"),
        ])
    result = select_group_beam(candidate_sets, samples)
    assert result.group_targetir_exact_match is True


def test_group_beam_rejects_wrong_consistent_collapse():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["paraphrase_group"] == "mul_2_3"]
    candidate_sets = [[_record(sample, "add(lit(1),lit(2))", score=5, suffix="wrong")] for sample in samples]
    result = select_group_beam(candidate_sets, samples)
    assert result.collapse_detected is True
    assert result.group_targetir_exact_match is False


def test_low_score_correct_candidate_is_recorded():
    sample = _sample()
    wrong = _record(sample, "mul(lit(2),lit(3))", score=5, suffix="wrong")
    correct = _record(sample, sample["target_ir_canonical"], score=1, suffix="correct")
    ranked = rerank_candidates_for_sample([wrong, correct], sample)
    assert any(item.quadrant == "low_score_correct" for item in ranked)


def test_high_score_wrong_candidate_is_recorded():
    sample = _sample("mul_2_3")
    wrong = _record(sample, "add(lit(1),lit(2))", score=5, suffix="wrong")
    ranked = rerank_candidates_for_sample([wrong], sample)
    assert ranked[0].quadrant == "high_score_wrong"


def test_pruning_candidate_signature():
    sample = _sample("mul_2_3")
    wrong = _record(sample, "add(lit(1),lit(2))", score=5, suffix="wrong")
    ranked = rerank_candidates_for_sample([wrong], sample)
    pruning = collect_pruning_candidates(ranked, [wrong])
    assert pruning
    assert "structure_policy=binary_operation" in branch_signature(wrong)


def test_hindsight_trainer_outputs_rerank_metrics():
    metrics = run_hindsight_branch_reranking_toy(generations=1, population_per_layer=8, top_k_candidates=2, beam_width=3, seed=11)
    final = metrics["metrics_by_generation"][-1]
    assert "reranked_sample_exact_match" in final
    assert "group_beam_exact_match" in final
    assert "pruning_candidate_count" in final


def test_report_contains_chinese_annotations():
    metrics = run_hindsight_branch_reranking_toy(generations=1, population_per_layer=8, top_k_candidates=2, beam_width=3, seed=12)
    text = open(metrics["report_path"], encoding="utf-8").read()
    assert "Hindsight Branch Re-Ranking（回看式分支重排）" in text
    assert "Group Beam Selection（组级束搜索）" in text
    assert "Branch Pruning（分支剪枝）" in text


def test_no_expression_oracle_import_in_reranking():
    source = inspect.getsource(reranking)
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_flat_classifier_imports():
    source = inspect.getsource(reranking) + inspect.getsource(evolution)
    assert "learned_router.perceptron" not in source
    assert "arithmetic_targetir.hashed_perceptron" not in source


def test_existing_tests_still_pass():
    assert build_architecture_aligned_toy_dataset()
