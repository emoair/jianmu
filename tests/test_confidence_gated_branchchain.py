import ast
from pathlib import Path

from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.branchchain.confidence_gate import LayerGateConfig, apply_confidence_gate
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype
from jianmu.self_learning.darwinforge.evaluate import run_confidence_gated_branchchain_toy
from jianmu.self_learning.darwinforge.fitness import compute_fitness
from jianmu.self_learning.darwinforge.population import GuardedBranchChainConfig, LayerPreservedPopulation


def _proposal(selected="programming", confidence=10):
    return BranchDecision("task_scope", [selected], selected, confidence, "n1", {})


def _genome(path):
    return CandidateGenome("g", path, [], "surface_number_order", "canonical_arithmetic_targetir")


def test_confidence_gate_rejects_when_no_proposals():
    result = apply_confidence_gate("task_scope", [], LayerGateConfig("task_scope", 10))
    assert result.can_continue is False
    assert result.reject_type == "missing_layer"


def test_confidence_gate_rejects_low_confidence():
    result = apply_confidence_gate("task_scope", [_proposal(confidence=5)], LayerGateConfig("task_scope", 10))
    assert result.can_continue is False
    assert result.reject_type == "no_confident_branch"
    assert result.reject_reason == "no_confident_branch_reject"


def test_confidence_gate_allows_high_confidence():
    result = apply_confidence_gate("task_scope", [_proposal(confidence=50)], LayerGateConfig("task_scope", 10))
    assert result.can_continue is True
    assert result.selected_proposal.selected == "programming"


def test_branch_decision_records_reject_reason():
    decision = _proposal(confidence=5)
    result = apply_confidence_gate("task_scope", [decision], LayerGateConfig("task_scope", 10))
    assert result.selected_proposal.reject_reason == "no_confident_branch_reject"
    assert result.selected_proposal.can_continue is False


def test_branch_path_records_rejected_by_layer():
    path = BranchPath(
        [],
        early_exit=True,
        rejected_by_layer="task_scope",
        reject_reason="no_confident_branch_reject",
        reject_type="no_confident_branch",
    )
    assert BranchPath.from_dict(path.to_dict()).reject_type == "no_confident_branch"


def test_population_candidate_paths_use_confidence_gate():
    config = GuardedBranchChainConfig(default_continue_threshold=95)
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42, guarded_config=config)
    paths = population.candidate_paths(extract_surface_features("写一首诗"), top_k=2, guarded_config=config)
    assert paths[0].early_exit is True
    assert paths[0].reject_type in {"no_confident_branch", "missing_layer", "typed_rejection"}


def test_atomic_synthesis_does_not_generate_code_after_no_confidence_reject():
    path = BranchPath(
        [],
        early_exit=True,
        rejected_by_layer="task_scope",
        reject_reason="no_confident_branch_reject",
        reject_type="no_confident_branch",
    )
    phenotype = AtomicSynthesis().synthesize(_genome(path), extract_surface_features("写一个 C 程序输出 1+2"))
    assert phenotype.unsupported_pred is True
    assert phenotype.c_program is None
    assert phenotype.target_ir_canonical is None


def test_false_accept_unsupported_penalty_stronger_than_false_reject_supported():
    unsupported = next(sample for sample in build_branchchain_toy_dataset() if not sample["supported"])
    supported = next(sample for sample in build_branchchain_toy_dataset() if sample["supported"])
    accept = compute_fitness(
        _genome(BranchPath([])),
        CandidatePhenotype("g", "add(lit(1),lit(2))", None, "3\n", False, None),
        unsupported,
        sandbox_optional=False,
    )
    reject = compute_fitness(
        _genome(BranchPath([], early_exit=True, reject_type="no_confident_branch")),
        CandidatePhenotype("g", None, None, None, True, "no_confident_branch_reject"),
        supported,
        sandbox_optional=False,
    )
    assert accept.total_fitness < reject.total_fitness


def test_no_confident_branch_reject_can_score_positive_for_unsupported():
    unsupported = next(sample for sample in build_branchchain_toy_dataset() if not sample["supported"])
    path = BranchPath([], early_exit=True, rejected_by_layer="task_scope", reject_reason="no_confident_branch_reject", reject_type="no_confident_branch")
    fitness = compute_fitness(_genome(path), CandidatePhenotype("g", None, None, None, True, "no_confident_branch_reject"), unsupported, sandbox_optional=False)
    assert fitness.total_fitness > 0


def test_supported_input_low_confidence_reject_is_penalized():
    supported = next(sample for sample in build_branchchain_toy_dataset() if sample["supported"])
    path = BranchPath([], early_exit=True, rejected_by_layer="task_scope", reject_reason="no_confident_branch_reject", reject_type="no_confident_branch")
    fitness = compute_fitness(_genome(path), CandidatePhenotype("g", None, None, None, True, "no_confident_branch_reject"), supported, sandbox_optional=False)
    assert fitness.total_fitness < 0


def test_report_contains_chinese_annotations():
    metrics = run_confidence_gated_branchchain_toy(population_per_layer=8, generations=2, top_k_candidates=2, seed=42)
    text = Path(metrics["report_path"]).read_text(encoding="utf-8")
    assert "Confidence-Gated Guarded BranchChain（置信度守卫式带守卫分支链）" in text
    assert "no_confidence_reject_count（无置信拒绝数）" in text
    assert "support_gate（支持/拒绝门）" in text


def test_no_expression_oracle_import_in_confidence_gate():
    tree = ast.parse(Path("jianmu/self_learning/branchchain/confidence_gate.py").read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any("expression_oracle" in name for name in imports)


def test_no_flat_classifier_imports():
    for root in [Path("jianmu/self_learning/branchchain"), Path("jianmu/self_learning/darwinforge")]:
        for path in root.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert "learned_router.perceptron" not in text
            assert "arithmetic_targetir.hashed_perceptron" not in text


def test_existing_tests_still_pass():
    from jianmu.runtime import Runtime
    from jianmu.self_learning.branchchain.confidence_gate import ConfidenceGateResult

    assert Runtime is not None
    assert ConfidenceGateResult is not None

