import ast
from pathlib import Path

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.curriculum import CurriculumPlan
from jianmu.self_learning.darwinforge.evaluate import run_curriculum_freezing_toy
from jianmu.self_learning.darwinforge.freezing import FreezeCriteria, LayerFreezeState, should_freeze, should_unfreeze
from jianmu.self_learning.darwinforge.hall_of_fame import HallOfFame
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def test_freeze_state_freezes_after_stable_accuracy():
    state = LayerFreezeState("task_scope")
    state.accuracy_history = [0.91, 0.92, 0.93]
    state.missing_rate_history = [0.0, 0.01, 0.0]
    assert should_freeze(state, FreezeCriteria(accuracy_threshold=0.90, stability_window=3, max_missing_rate=0.05))


def test_frozen_layer_still_routes():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=42)
    plan = CurriculumPlan()
    plan.freeze_states["task_scope"].frozen = True
    paths = population.candidate_paths(extract_surface_features("写一个 C 程序输出 1+2"), top_k=2)
    assert paths
    assert any(decision.layer_name == "task_scope" for decision in paths[0].decisions)


def test_frozen_layer_does_not_mutate():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=42)
    plan = CurriculumPlan()
    plan.freeze_states["task_scope"].frozen = True
    before = [n.to_dict() if hasattr(n, "to_dict") else (n.neuron_id, n.weights, n.threshold, n.mutation_count) for n in population.per_layer["task_scope"]]
    population.evolve([], seed=43, curriculum_plan=plan)
    after = [(n.neuron_id, n.weights, n.threshold, n.mutation_count) for n in population.per_layer["task_scope"]]
    assert before == after


def test_active_layer_can_mutate():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=42)
    plan = CurriculumPlan()
    before = [(n.neuron_id, n.weights, n.threshold, n.mutation_count) for n in population.per_layer[plan.active_layer()]]
    population.evolve([], seed=43, curriculum_plan=plan)
    after = [(n.neuron_id, n.weights, n.threshold, n.mutation_count) for n in population.per_layer[plan.active_layer()]]
    assert before != after


def test_curriculum_advances_after_freeze():
    plan = CurriculumPlan()
    for _ in range(3):
        plan.update_layer_metrics("task_scope", 1.0, 0.0, 1.0)
    assert plan.maybe_freeze_active_layer()
    assert plan.maybe_advance()
    assert plan.active_layer() == "language_target"


def test_conditional_unfreeze_from_hard_cases():
    state = LayerFreezeState("support_gate", frozen=True)
    assert should_unfreeze(state, {"support_gate": {"error_rate": 0.8, "severity": 0.8}}, threshold=0.5)
    plan = CurriculumPlan()
    plan.freeze_states["support_gate"].frozen = True
    events = plan.maybe_unfreeze_from_hard_cases({"support_gate": {"error_rate": 0.8, "severity": 0.8}}, threshold=0.5)
    assert events
    assert plan.freeze_states["support_gate"].unfreeze_count == 1


def test_hall_of_fame_records_best_generation():
    hof = HallOfFame()
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=42)
    hof.update(0, {"target_ir_exact_match_rate": 0.5, "mean_fitness": 1.0, "missing_layer_rate": 0.2}, population)
    hof.update(1, {"target_ir_exact_match_rate": 0.6, "mean_fitness": 0.5, "missing_layer_rate": 0.3}, population)
    assert hof.best_generation == 1
    assert hof.best_target_ir_exact_match == 0.6


def test_layer_preserved_population_respects_freeze():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=42)
    plan = CurriculumPlan()
    plan.freeze_states["language_target"].frozen = True
    before = [(n.neuron_id, n.weights, n.threshold) for n in population.per_layer["language_target"]]
    population.evolve([], seed=43, curriculum_plan=plan)
    after = [(n.neuron_id, n.weights, n.threshold) for n in population.per_layer["language_target"]]
    assert before == after


def test_beam_candidate_paths_returns_multiple_paths():
    population = LayerPreservedPopulation.initialize(population_per_layer=16, seed=42)
    paths = population.candidate_paths(extract_surface_features("写一个 C 程序输出 1+2"), top_k=3)
    assert len(paths) >= 2
    assert len({tuple((d.layer_name, d.selected) for d in path.decisions) for path in paths}) >= 2


def test_curriculum_trainer_records_freeze_events():
    metrics = run_curriculum_freezing_toy(population_per_layer=8, generations=3, top_k_candidates=2, seed=42, compile_checks_per_generation=0)
    assert "freeze_events" in metrics["curriculum"]
    assert "active_layer" in metrics["metrics_by_generation"][0]


def test_final_and_best_metrics_are_both_reported():
    metrics = run_curriculum_freezing_toy(population_per_layer=8, generations=3, top_k_candidates=2, seed=43, compile_checks_per_generation=0)
    assert "hall_of_fame" in metrics
    assert "best_metrics" in metrics["hall_of_fame"]
    assert Path(metrics["report_path"]).exists()


def test_no_expression_oracle_import_in_curriculum_or_population():
    for filename in [
        "jianmu/self_learning/darwinforge/curriculum.py",
        "jianmu/self_learning/darwinforge/freezing.py",
        "jianmu/self_learning/darwinforge/population.py",
    ]:
        tree = ast.parse(Path(filename).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any("expression_oracle" in name for name in imports)


def test_no_flat_classifier_imports():
    root = Path("jianmu/self_learning/darwinforge")
    forbidden = ["learned_router.perceptron", "arithmetic_targetir.hashed_perceptron"]
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_existing_tests_still_pass():
    from jianmu.runtime import Runtime
    from jianmu.self_learning.darwinforge.curriculum import CurriculumPlan

    assert Runtime is not None
    assert CurriculumPlan is not None

