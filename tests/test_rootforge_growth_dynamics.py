from pathlib import Path

from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome
from jianmu.self_learning.darwinforge.path_diagnostics import diagnose_paths
from jianmu.self_learning.darwinforge.rootforge_growth_trainer import RootForgeGrowthConfig, RootForgeGrowthTrainer, write_rootforge_outputs
from jianmu.self_learning.datasets.symbol_grounding import build_symbol_grounding_dataset
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def _genome(decisions):
    path = BranchPath(
        decisions=[
            BranchDecision(layer_name=layer, candidates=[selected], selected=selected, confidence=60, neuron_id=f"{layer}:{selected}", evidence={})
            for layer, selected in decisions
        ],
        route_confidence=60,
        atomic_experts=["ArithmeticExpressionExpert"],
        target_builder="canonical_arithmetic_targetir",
    )
    return CandidateGenome(
        genome_id="g",
        branch_path=path,
        atomic_expert_plan=path.atomic_experts,
        slot_binding_policy="surface_number_order",
        target_builder_policy="canonical_arithmetic_targetir",
    )


def test_atomic_synthesis_literal_only():
    genome = _genome(
        [
            ("task_scope", "programming"),
            ("language_target", "math_expression_context"),
            ("semantic_domain", "arithmetic"),
            ("arithmetic_family", "literal_only"),
            ("structure_policy", "literal_value"),
            ("slot_binding_policy", "signed_number_order"),
            ("target_builder", "canonical_arithmetic_targetir"),
        ]
    )

    phenotype = AtomicSynthesis().synthesize(genome, {"signed_numbers": [-6], "operator_sequence": ""})

    assert phenotype.target_ir_canonical == "lit(-6)"
    assert phenotype.expected_output_pred == "-6\n"


def test_atomic_synthesis_precedence_div_then_add():
    genome = _genome(
        [
            ("task_scope", "programming"),
            ("language_target", "math_expression_context"),
            ("semantic_domain", "arithmetic"),
            ("arithmetic_family", "mixed_precedence"),
            ("structure_policy", "precedence_tree"),
            ("slot_binding_policy", "surface_number_order"),
            ("target_builder", "canonical_arithmetic_targetir"),
        ]
    )

    phenotype = AtomicSynthesis().synthesize(genome, {"signed_numbers": [24, 4, 3], "operator_sequence": "/+"})

    assert phenotype.target_ir_canonical == "add(div(lit(24),lit(4)),lit(3))"
    assert phenotype.expected_output_pred == "9\n"


def test_atomic_synthesis_parenthesized_add_then_div():
    genome = _genome(
        [
            ("task_scope", "programming"),
            ("language_target", "math_expression_context"),
            ("semantic_domain", "arithmetic"),
            ("arithmetic_family", "parentheses"),
            ("structure_policy", "parenthesized_tree"),
            ("slot_binding_policy", "surface_number_order"),
            ("target_builder", "canonical_arithmetic_targetir"),
        ]
    )

    phenotype = AtomicSynthesis().synthesize(genome, {"signed_numbers": [3, 5, 4], "operator_sequence": "+/"})

    assert phenotype.target_ir_canonical == "div(add(lit(3),lit(5)),lit(4))"
    assert phenotype.expected_output_pred == "2\n"


def test_canonicalizer_strips_dataset_artifact_suffix():
    result = canonicalize_symbols("24/4+3（jm-v070-002202）")

    assert result.raw_text == "24/4+3（jm-v070-002202）"
    assert result.canonical_text == "24/4+3"
    assert "stripped_dataset_artifact_suffix" in result.warnings


def test_path_diagnostics_ignores_optional_support_gate():
    sample = {
        "sample_id": "s",
        "input_text": "1+2",
        "supported": True,
        "target_ir_canonical": "add(lit(1),lit(2))",
        "target_branch_path": [
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", "addition"],
            ["structure_policy", "binary_operation"],
            ["slot_binding_policy", "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
    }
    genome = _genome(
        [
            ("task_scope", "programming"),
            ("language_target", "math_expression_context"),
            ("semantic_domain", "arithmetic"),
            ("support_gate", "supported"),
            ("arithmetic_family", "addition"),
            ("structure_policy", "binary_operation"),
            ("slot_binding_policy", "surface_number_order"),
            ("target_builder", "canonical_arithmetic_targetir"),
        ]
    )
    phenotype = AtomicSynthesis().synthesize(genome, {"signed_numbers": [1, 2], "operator_sequence": "+"})
    from jianmu.self_learning.darwinforge.fitness import compute_fitness
    from jianmu.self_learning.darwinforge.candidate import CandidateRecord

    record = CandidateRecord(genome, phenotype, compute_fitness(genome, phenotype, sample, sandbox_optional=False))

    diagnostic = diagnose_paths(sample, [record])

    assert diagnostic.correct_path_in_beam is True


def test_rootforge_trainer_quick_mode_runs(tmp_path):
    dataset = build_symbol_grounding_dataset(size=120, seed=42)
    train = dataset["train"][:24]
    eval_samples = dataset["eval"][:12]
    ood = dataset["ood"][:8]
    config = RootForgeGrowthConfig.for_mode("quick", train_limit=24, eval_limit=12, ood_limit=8, generations=1, beam_size=8, population_per_layer=8)

    metrics = RootForgeGrowthTrainer(train, eval_samples, ood, config).train()
    paths = write_rootforge_outputs(metrics, tmp_path)

    assert "literal_only_targetir_exact_match" in metrics
    assert "necrosis_candidate_count" in metrics
    assert Path(paths["report_path"]).exists()


def test_report_contains_chinese_annotations(tmp_path):
    dataset = build_symbol_grounding_dataset(size=120, seed=7)
    train = dataset["train"][:12]
    eval_samples = dataset["eval"][:8]
    ood = dataset["ood"][:4]
    config = RootForgeGrowthConfig.for_mode("quick", train_limit=12, eval_limit=8, ood_limit=4, generations=1, beam_size=8, population_per_layer=8)

    metrics = RootForgeGrowthTrainer(train, eval_samples, ood, config).train()
    paths = write_rootforge_outputs(metrics, tmp_path)
    report = Path(paths["report_path"]).read_text(encoding="utf-8")

    assert "RootForge Growth Dynamics（根铸生长动力学）" in report
    assert "Nutrient" in report or "养分" in report


def test_no_expression_oracle_import():
    for path in [
        "jianmu/self_learning/darwinforge/rootforge.py",
        "jianmu/self_learning/darwinforge/rootforge_growth_trainer.py",
    ]:
        source = Path(path).read_text(encoding="utf-8")
        assert "expression_oracle" not in source
        assert "parse_controlled_expression" not in source


def test_no_external_api_calls():
    source = "\n".join(Path(path).read_text(encoding="utf-8") for path in Path("jianmu/self_learning/darwinforge").glob("root*.py"))
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source


def test_candidate_generation_does_not_use_targetir_or_target_branch_path():
    source = Path("jianmu/self_learning/darwinforge/beam_backtracking.py").read_text(encoding="utf-8")

    assert "target_ir" not in source
    assert "expected_output" not in source
    assert "target_branch_path" not in source
