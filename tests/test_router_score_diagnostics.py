from jianmu.self_learning.darwinforge.canonicalized_training_eval import build_training_features
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.router_score_diagnostics import find_fork_point, score_target_branch_path


TARGET_PATH = [
    ["task_scope", "programming"],
    ["language_target", "math_expression_context"],
    ["semantic_domain", "arithmetic"],
    ["arithmetic_family", "addition"],
    ["structure_policy", "binary_operation"],
    ["slot_binding_policy", "surface_number_order"],
    ["target_builder", "canonical_arithmetic_targetir"],
]


def test_score_target_branch_path_outputs_layer_scores():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)
    features = build_training_features("1+2", canonicalization_enabled=True)

    diag = score_target_branch_path(population, features, TARGET_PATH, proposals_per_layer=3)

    assert diag["layers"]
    first = diag["layers"][0]
    assert {"layer_name", "target_option", "target_option_score", "target_option_rank", "top_candidates"} <= set(first)
    assert "task_scope" in diag["correct_option_rank_by_layer"]


def test_find_fork_point_from_low_score_correct_layer():
    score_diag = {
        "layers": [
            {"layer_name": "task_scope", "target_option": "programming", "target_option_rank": 1, "score_gap_to_best": 0},
            {"layer_name": "arithmetic_family", "target_option": "addition", "target_option_rank": 5, "score_gap_to_best": 12},
        ],
        "first_low_score_correct_layer": "arithmetic_family",
    }

    fork = find_fork_point(score_diag, {})

    assert fork["fork_layer"] == "arithmetic_family"
    assert fork["fork_reason"] == "first_low_score_correct_layer"
    assert fork["stable_prefix"] == [["task_scope", "programming"]]


def test_find_fork_point_from_pruned_correct_layer():
    score_diag = {
        "layers": [
            {"layer_name": "task_scope", "target_option": "programming", "target_option_rank": 1, "score_gap_to_best": 0},
            {"layer_name": "structure_policy", "target_option": "precedence_tree", "target_option_rank": 8, "score_gap_to_best": 20},
        ],
        "first_low_score_correct_layer": "structure_policy",
        "first_pruned_correct_layer": "structure_policy",
    }

    fork = find_fork_point(score_diag, {})

    assert fork["fork_layer"] == "structure_policy"
    assert fork["fork_reason"] == "first_pruned_correct_layer"
    assert fork["target_option_rank"] == 8
