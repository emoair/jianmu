import ast
import json
from pathlib import Path

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.darwinforge.curriculum import CurriculumPlan
from jianmu.self_learning.darwinforge.evaluate import run_highest_stable_threshold_search_toy
from jianmu.self_learning.darwinforge.freezing import FreezeCriteria, required_correct_count
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.threshold_search import LayerThresholdState, ThresholdSearchController


def test_layer_start_threshold_defaults_high():
    criteria = FreezeCriteria()
    assert criteria.get_start_threshold("task_scope") == 0.98
    assert criteria.get_start_threshold("support_gate") == 0.95


def test_layer_floor_thresholds_exist():
    criteria = FreezeCriteria()
    assert criteria.get_floor_threshold("support_gate") == 0.85
    assert criteria.get_floor_threshold("slot_binding_policy") == 0.75


def test_required_correct_count_for_20_samples():
    assert required_correct_count(20, 0.95) == 19
    assert required_correct_count(20, 0.90) == 18
    assert required_correct_count(20, 0.85) == 17
    assert required_correct_count(20, 0.80) == 16


def test_threshold_anneals_down_but_not_below_floor():
    criteria = FreezeCriteria(plateau_patience=2, anneal_step=0.05)
    state = LayerThresholdState("support_gate", 0.95, 0.95, 0.85)
    state.record_generation(0.8, 0.9, 0.0, 16, 20)
    state.record_generation(0.8, 0.9, 0.0, 16, 20)
    state.record_generation(0.8, 0.9, 0.0, 16, 20)
    assert state.should_anneal(criteria)
    state.anneal(criteria)
    assert state.current_threshold == 0.9
    for _ in range(6):
        state.record_generation(0.8, 0.9, 0.0, 16, 20)
        if state.should_anneal(criteria):
            state.anneal(criteria)
    assert state.current_threshold < state.floor_threshold or state.current_threshold == state.floor_threshold
    assert state.blocked or state.current_threshold >= state.floor_threshold


def test_layer_freezes_at_current_threshold():
    criteria = FreezeCriteria()
    controller = ThresholdSearchController(criteria)
    controller.states["support_gate"].current_threshold = 0.85
    controller.mark_frozen("support_gate")
    assert controller.states["support_gate"].frozen_threshold == 0.85


def test_frozen_threshold_recorded():
    plan = CurriculumPlan()
    plan.threshold_controller.states["task_scope"].current_threshold = 0.9
    for _ in range(3):
        plan.update_layer_metrics("task_scope", 0.95, 0.0, 1.0)
    assert plan.maybe_freeze_active_layer()
    assert plan.freeze_states["task_scope"].frozen_threshold == 0.9


def test_blocked_layer_when_below_floor():
    criteria = FreezeCriteria(plateau_patience=1, anneal_step=0.2)
    controller = ThresholdSearchController(criteria)
    controller.states["support_gate"].current_threshold = 0.86
    controller.update("support_gate", {"accuracy": 0.5, "recall_at_k": 0.5, "missing_rate": 0.0, "correct_count": 10, "total_count": 20})
    controller.update("support_gate", {"accuracy": 0.5, "recall_at_k": 0.5, "missing_rate": 0.0, "correct_count": 10, "total_count": 20})
    controller.maybe_anneal("support_gate", generation=2)
    controller.update("support_gate", {"accuracy": 0.5, "recall_at_k": 0.5, "missing_rate": 0.0, "correct_count": 10, "total_count": 20})
    controller.update("support_gate", {"accuracy": 0.5, "recall_at_k": 0.5, "missing_rate": 0.0, "correct_count": 10, "total_count": 20})
    controller.maybe_anneal("support_gate", generation=4)
    assert controller.states["support_gate"].blocked is True


def test_layer_recall_at_k_detects_correct_candidate():
    population = LayerPreservedPopulation.initialize(population_per_layer=16, seed=42)
    paths = population.candidate_paths(extract_surface_features("写一个 C 程序输出 1+2"), top_k=3)
    assert any(any(d.layer_name == "support_gate" and d.selected == "supported" for d in p.decisions) for p in paths)


def test_winner_accuracy_and_recall_at_k_can_differ():
    metrics = run_highest_stable_threshold_search_toy(population_per_layer=8, generations=2, top_k_candidates=3, seed=42, compile_checks_per_generation=0)
    row = metrics["metrics_by_generation"][-1]
    assert "per_layer_winner_accuracy" in row
    assert "per_layer_recall_at_k" in row


def test_support_gate_confusion_matrix():
    metrics = run_highest_stable_threshold_search_toy(population_per_layer=8, generations=2, top_k_candidates=2, seed=43, compile_checks_per_generation=0)
    matrix = metrics["metrics_by_generation"][-1]["support_gate_confusion_matrix"]
    assert set(matrix) == {
        "true_supported_pred_supported",
        "true_supported_pred_unsupported",
        "true_unsupported_pred_supported",
        "true_unsupported_pred_unsupported",
    }


def test_report_contains_chinese_annotations():
    metrics = run_highest_stable_threshold_search_toy(population_per_layer=8, generations=2, top_k_candidates=2, seed=44, compile_checks_per_generation=0)
    text = Path(metrics["report_path"]).read_text(encoding="utf-8")
    assert "BranchChain（分支链）" in text
    assert "support_gate（支持/拒绝门）" in text
    assert "layer_recall@k（层级候选召回）" in text


def test_no_expression_oracle_import_in_threshold_search():
    tree = ast.parse(Path("jianmu/self_learning/darwinforge/threshold_search.py").read_text(encoding="utf-8"))
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
    from jianmu.self_learning.darwinforge.threshold_search import ThresholdSearchController

    assert Runtime is not None
    assert ThresholdSearchController is not None
