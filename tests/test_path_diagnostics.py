from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype, CandidateRecord
from jianmu.self_learning.darwinforge.fitness import FitnessReport
from jianmu.self_learning.darwinforge.path_diagnostics import diagnose_paths


TARGET_PATH = [
    ["task_scope", "programming"],
    ["language_target", "math_expression_context"],
    ["semantic_domain", "arithmetic"],
    ["arithmetic_family", "addition"],
    ["structure_policy", "binary_operation"],
    ["slot_binding_policy", "surface_number_order"],
    ["target_builder", "canonical_arithmetic_targetir"],
]


def _sample():
    return {
        "sample_id": "s1",
        "input_text": "1+2",
        "supported": True,
        "target_ir_canonical": "add(lit(1),lit(2))",
        "target_branch_path": TARGET_PATH,
    }


def _record(selected_by_layer, target_ir, fitness, rejected_by_layer=None):
    decisions = [
        BranchDecision(layer_name=layer, candidates=[selected], selected=selected, confidence=50, neuron_id=f"{layer}:{selected}", evidence={"source_clone_id": "base"})
        for layer, selected in selected_by_layer
    ]
    path = BranchPath(
        decisions=decisions,
        route_confidence=50,
        atomic_experts=[] if rejected_by_layer else ["ArithmeticExpressionExpert"],
        target_builder=decisions[-1].selected if decisions else "early_exit",
        early_exit=bool(rejected_by_layer),
        rejected_by_layer=rejected_by_layer,
        reject_reason="no_confident_branch_reject" if rejected_by_layer else None,
        reject_type="no_confident_branch" if rejected_by_layer else None,
    )
    genome = CandidateGenome(
        genome_id=f"g-{fitness}",
        branch_path=path,
        atomic_expert_plan=path.atomic_experts,
        slot_binding_policy="surface_number_order",
        target_builder_policy="canonical_arithmetic_targetir",
    )
    phenotype = CandidatePhenotype(
        genome_id=genome.genome_id,
        target_ir_canonical=target_ir,
        c_program=None,
        expected_output_pred=None,
        unsupported_pred=bool(rejected_by_layer),
        failure_reason=None,
    )
    report = FitnessReport(
        total_fitness=fitness,
        target_ir_similarity=0.0,
        target_ir_exact_match=target_ir == "add(lit(1),lit(2))",
        expected_output_match=False,
        compile_success=None,
        run_success=None,
        unsupported_correct=False,
        invalid_targetir_penalty=0.0,
        wrong_output_penalty=0.0,
        path_length_penalty=0.0,
        efficiency_bonus=0.0,
        components={},
    )
    return CandidateRecord(genome, phenotype, report)


def test_diagnose_correct_targetir_in_beam():
    records = [
        _record(TARGET_PATH, "add(lit(1),lit(2))", 10.0),
        _record(TARGET_PATH[:-3] + [["arithmetic_family", "multiplication"]], "mul(lit(1),lit(2))", 1.0),
    ]

    diagnostic = diagnose_paths(_sample(), records)

    assert diagnostic.correct_targetir_in_beam is True
    assert diagnostic.best_beam_exact is True
    assert diagnostic.top1_exact is True


def test_diagnose_ranking_failure():
    records = [
        _record(TARGET_PATH[:-3] + [["arithmetic_family", "multiplication"]], "mul(lit(1),lit(2))", 10.0),
        _record(TARGET_PATH, "add(lit(1),lit(2))", 1.0),
    ]

    diagnostic = diagnose_paths(_sample(), records)

    assert diagnostic.correct_targetir_in_beam is True
    assert diagnostic.top1_exact is False
    assert diagnostic.ranking_failure is True


def test_diagnose_candidate_space_failure():
    records = [_record(TARGET_PATH[:-3] + [["arithmetic_family", "multiplication"]], "mul(lit(1),lit(2))", 10.0)]

    diagnostic = diagnose_paths(_sample(), records)

    assert diagnostic.candidate_space_failure is True
    assert diagnostic.correct_targetir_in_beam is False


def test_diagnose_upstream_boundary_failure():
    wrong_path = [["task_scope", "reject_non_programming"]]
    records = [_record(wrong_path, None, 10.0, rejected_by_layer="task_scope")]

    diagnostic = diagnose_paths(_sample(), records)

    assert diagnostic.upstream_boundary_failure is True
    assert diagnostic.first_wrong_layer == "task_scope"


def test_diagnose_synthesis_failure():
    records = [_record(TARGET_PATH, "sub(lit(1),lit(2))", 10.0)]

    diagnostic = diagnose_paths(_sample(), records)

    assert diagnostic.correct_path_in_beam is True
    assert diagnostic.correct_targetir_in_beam is False
    assert diagnostic.synthesis_failure is True


def test_first_wrong_layer_detection():
    wrong_path = TARGET_PATH[:3] + [["arithmetic_family", "multiplication"]]
    records = [_record(wrong_path, "mul(lit(1),lit(2))", 10.0)]

    diagnostic = diagnose_paths(_sample(), records)

    assert diagnostic.first_wrong_layer == "arithmetic_family"
    assert diagnostic.first_wrong_expected == "addition"
    assert diagnostic.first_wrong_actual == "multiplication"
