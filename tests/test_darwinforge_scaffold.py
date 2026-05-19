import ast
from pathlib import Path

from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype
from jianmu.self_learning.darwinforge.evolution import DarwinForgeTrainer
from jianmu.self_learning.darwinforge.fitness import FitnessReport, compute_fitness
from jianmu.self_learning.darwinforge.hard_cases import HardCase, HardCaseBuffer
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def _path(structure_policy="binary_operation", support_gate="supported"):
    layers = [
        ("task_scope", "programming"),
        ("language_target", "C"),
        ("semantic_domain", "arithmetic"),
        ("support_gate", support_gate),
        ("arithmetic_family", "addition"),
        ("structure_policy", structure_policy),
        ("slot_binding_policy", "surface_number_order"),
        ("target_builder", "canonical_arithmetic_targetir"),
    ]
    decisions = [BranchDecision(layer, [selected], selected, 90, f"n:{layer}", {}) for layer, selected in layers]
    return BranchPath(decisions, 90, ["ArithmeticExpressionExpert"], "canonical_arithmetic_targetir", support_gate == "unsupported", None)


def _genome(structure_policy="binary_operation", support_gate="supported"):
    return CandidateGenome(
        genome_id="g1",
        branch_path=_path(structure_policy, support_gate),
        atomic_expert_plan=["ArithmeticExpressionExpert"],
        slot_binding_policy="surface_number_order",
        target_builder_policy="canonical_arithmetic_targetir",
    )


def test_candidate_genome_serialization():
    genome = _genome()
    restored = CandidateGenome.from_dict(genome.to_dict())
    assert restored.to_dict() == genome.to_dict()


def test_atomic_synthesis_oracle_free(monkeypatch):
    from jianmu.self_learning.arithmetic_targetir import expression_oracle

    monkeypatch.setattr(expression_oracle, "parse_controlled_expression", lambda *_: (_ for _ in ()).throw(RuntimeError("oracle forbidden")))
    phenotype = AtomicSynthesis().synthesize(_genome(), extract_surface_features("写一个 C 程序输出 1+2"))
    assert phenotype.target_ir_canonical == "add(lit(1),lit(2))"
    assert phenotype.expected_output_pred == "3\n"


def test_atomic_synthesis_depends_on_branch_path():
    features = extract_surface_features("写程序计算 1+2*3")
    binary = AtomicSynthesis().synthesize(_genome("binary_operation"), features)
    precedence = AtomicSynthesis().synthesize(_genome("precedence_tree"), features)
    assert binary.target_ir_canonical != precedence.target_ir_canonical


def test_fitness_rewards_target_ir_match():
    target = build_branchchain_toy_dataset()[0]
    genome = _genome()
    phenotype = CandidatePhenotype("g1", target["target_ir_canonical"], None, target["expected_output"], False, None)
    fitness = compute_fitness(genome, phenotype, target, sandbox_optional=False)
    assert fitness.target_ir_exact_match is True
    assert fitness.total_fitness > 5


def test_fitness_penalizes_unsupported_generation():
    target = next(sample for sample in build_branchchain_toy_dataset() if not sample["supported"])
    genome = _genome()
    phenotype = CandidatePhenotype("g1", "add(lit(1),lit(2))", None, "3\n", False, None)
    fitness = compute_fitness(genome, phenotype, target, sandbox_optional=False)
    assert fitness.components["unsupported_generated"] is True
    assert fitness.total_fitness < 0


def test_layer_preserved_population_keeps_all_layers():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)
    assert all(len(neurons) >= 8 for neurons in population.per_layer.values())


def test_layer_preserved_population_keeps_option_coverage():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=42)
    for layer_name, neurons in population.per_layer.items():
        assert {n.option for n in neurons}
    population.evolve([], seed=43)
    for layer_name, neurons in population.per_layer.items():
        assert {n.option for n in neurons}


def test_darwinforge_trainer_records_metrics():
    trainer = DarwinForgeTrainer(population_per_layer=8, generations=2, top_k_candidates=2, seed=42)
    report = trainer.train(build_branchchain_toy_dataset())
    assert len(report.metrics_by_generation) == 3
    assert "mean_fitness" in report.metrics_by_generation[0]
    assert "missing_layer_rate" in report.metrics_by_generation[0]


def test_hard_case_buffer_records_failures(tmp_path):
    buffer = HardCaseBuffer()
    buffer.add(HardCase("x", "target", "1\n", None, -1.0, "fail", 0, {"a": 1}))
    path = tmp_path / "hard.jsonl"
    buffer.save_jsonl(path)
    restored = HardCaseBuffer.load_jsonl(path)
    assert len(restored.items) == 1
    assert restored.items[0].failure_reason == "fail"


def test_no_old_source_patch_fields():
    genome = _genome().to_dict()
    phenotype = CandidatePhenotype("g1", None, None, None, True, None).to_dict()
    text = str(genome) + str(phenotype)
    assert "patch" not in text.lower()
    assert "diff" not in text.lower()


def test_no_flat_classifier_imports():
    root = Path("jianmu/self_learning/darwinforge")
    forbidden = ["learned_router.perceptron", "arithmetic_targetir.hashed_perceptron"]
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_no_expression_oracle_import_in_candidate_generation():
    root = Path("jianmu/self_learning/darwinforge")
    modules = ["candidate.py", "atomic_synthesis.py", "population.py", "evolution.py"]
    for filename in modules:
        tree = ast.parse((root / filename).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any("expression_oracle" in name for name in imports)


def test_existing_tests_still_pass():
    from jianmu.runtime import Runtime
    from jianmu.self_learning.branchchain.branch_types import BranchPath

    assert Runtime is not None
    assert BranchPath is not None

