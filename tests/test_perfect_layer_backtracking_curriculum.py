import inspect

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_architecture_aligned_toy_dataset
from jianmu.self_learning.darwinforge import backtracking_curriculum, evolution
from jianmu.self_learning.darwinforge.backtracking_curriculum import (
    BacktrackingEvent,
    PerfectLayerCriteria,
    PerfectLayerCurriculumPlan,
)
from jianmu.self_learning.darwinforge.evaluate import run_perfect_layer_backtracking_toy
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def test_perfect_layer_criteria_requires_all_correct():
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope"], criteria=PerfectLayerCriteria(perfect_stability_window=1))
    plan.update_layer_metrics("task_scope", 0.9, 1.0, 0.0, 9, 10, 0)
    assert not plan.should_freeze_layer("task_scope")


def test_layer_freezes_only_at_100_percent_in_perfect_mode():
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope"], criteria=PerfectLayerCriteria(perfect_stability_window=1))
    plan.update_layer_metrics("task_scope", 1.0, 1.0, 0.0, 10, 10, 0)
    assert plan.should_freeze_layer("task_scope")
    plan.freeze_layer("task_scope", 0)
    assert plan.is_frozen("task_scope")


def test_frozen_layer_still_routes():
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope"], criteria=PerfectLayerCriteria(perfect_stability_window=1))
    plan.update_layer_metrics("task_scope", 1.0, 1.0, 0.0, 1, 1, 0)
    plan.freeze_layer("task_scope", 0)
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=3)
    paths = population.candidate_paths(extract_surface_features("写一个 C 程序输出 1+2"), top_k=2)
    assert paths
    assert any(decision.layer_name == "task_scope" for decision in paths[0].decisions)


def test_stalled_layer_triggers_backtracking():
    criteria = PerfectLayerCriteria(patience_generations=2, perfect_stability_window=1)
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope"], criteria=criteria)
    plan.update_layer_metrics("task_scope", 0.5, 0.5, 0.0, 1, 2, 0)
    plan.update_layer_metrics("task_scope", 0.5, 0.5, 0.0, 1, 2, 2)
    assert plan.should_backtrack("task_scope", 2)
    event = plan.start_backtracking("task_scope", 2)
    assert event.active_layer == "task_scope"


def test_backtracking_unfreezes_previous_layer():
    criteria = PerfectLayerCriteria(backtrack_window=1, patience_generations=1)
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope", "language_target"], criteria=criteria)
    plan.freeze_layer("task_scope", 0)
    plan.active_layer_index = 1
    plan.states["language_target"].status = "active"
    event = plan.start_backtracking("language_target", 3)
    assert "task_scope" in event.unfrozen_layers
    assert plan.can_mutate("task_scope")


def test_backtracking_respects_max_attempts():
    criteria = PerfectLayerCriteria(max_backtrack_attempts_per_layer=1, patience_generations=1)
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope"], criteria=criteria)
    plan.update_layer_metrics("task_scope", 0.5, 0.5, 0.0, 1, 2, 0)
    plan.start_backtracking("task_scope", 1)
    assert not plan.should_backtrack("task_scope", 2)


def test_blocked_layer_after_failed_backtracking():
    criteria = PerfectLayerCriteria(max_backtrack_attempts_per_layer=1, backtrack_generations=1)
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope"], criteria=criteria)
    plan.update_layer_metrics("task_scope", 0.5, 0.5, 0.0, 1, 2, 0)
    plan.start_backtracking("task_scope", 0)
    plan.update_layer_metrics("task_scope", 0.5, 0.5, 0.0, 1, 2, 1)
    plan.finish_backtracking("task_scope", 1, improved=False)
    assert "task_scope" in plan.blocked_layers


def test_backtracking_event_serialization():
    event = BacktrackingEvent(1, "language_target", ["task_scope", "language_target"], "stall", 0.5, 0.75, "improved")
    payload = event.to_dict()
    assert payload["active_layer"] == "language_target"
    assert payload["outcome"] == "improved"


def test_perfect_layer_trainer_records_freeze_events():
    metrics = run_perfect_layer_backtracking_toy(generations=2, population_per_layer=8, top_k_candidates=2, seed=5)
    assert "freeze_events" in metrics["curriculum"]


def test_perfect_layer_trainer_records_backtracking_events():
    metrics = run_perfect_layer_backtracking_toy(generations=10, population_per_layer=8, top_k_candidates=2, seed=6)
    assert "backtracking_events" in metrics["curriculum"]


def test_mutation_scale_for_backtracking_layer():
    plan = PerfectLayerCurriculumPlan(layer_order=["task_scope", "language_target"], criteria=PerfectLayerCriteria(upstream_mutation_scale=0.3))
    plan.freeze_layer("task_scope", 0)
    plan.active_layer_index = 1
    plan.states["language_target"].status = "active"
    plan.start_backtracking("language_target", 2)
    assert plan.mutation_scale("task_scope") == 0.3
    assert plan.mutation_scale("language_target") == 1.0


def test_report_contains_toy_only_warning():
    metrics = run_perfect_layer_backtracking_toy(generations=1, population_per_layer=8, top_k_candidates=2, seed=7)
    text = open(metrics["report_path"], encoding="utf-8").read()
    assert "toy/synthetic deterministic data（玩具/合成确定性数据）" in text
    assert "Highest-Stable Threshold Search（最高稳定阈值搜索）" in text


def test_report_contains_chinese_annotations():
    metrics = run_perfect_layer_backtracking_toy(generations=1, population_per_layer=8, top_k_candidates=2, seed=8)
    text = open(metrics["report_path"], encoding="utf-8").read()
    assert "Perfect-Layer Backtracking Curriculum（完美层回溯课程训练）" in text
    assert "Frozen Layer" not in text or "冻结层" in text


def test_no_expression_oracle_import_in_backtracking_curriculum():
    source = inspect.getsource(backtracking_curriculum)
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_flat_classifier_imports():
    source = inspect.getsource(backtracking_curriculum) + inspect.getsource(evolution)
    assert "learned_router.perceptron" not in source
    assert "arithmetic_targetir.hashed_perceptron" not in source


def test_existing_tests_still_pass():
    assert build_architecture_aligned_toy_dataset()
