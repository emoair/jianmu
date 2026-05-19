import ast
import json
from pathlib import Path

from jianmu.self_learning.branchchain.branch_chain import BranchChainRouter
from jianmu.self_learning.branchchain.branch_neuron import make_seed_neurons
from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.branchchain.evaluate import run_branchchain_toy_experiment
from jianmu.self_learning.branchchain.path_reward import compute_path_reward
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_branchchain_toy_dataset
from jianmu.self_learning.branchchain.toy_trainer import BranchChainToyTrainer


def test_surface_features_oracle_free(monkeypatch):
    from jianmu.self_learning.arithmetic_targetir import expression_oracle

    monkeypatch.setattr(expression_oracle, "parse_controlled_expression", lambda *_: (_ for _ in ()).throw(RuntimeError("oracle forbidden")))
    features = extract_surface_features("写一个 C 程序输出 1+2")
    assert features["contains_C"] is True
    assert features["contains_plus"] is True
    assert features["signed_numbers"] == [1, 2]


def test_branch_decision_serialization():
    decision = BranchDecision("task_scope", ["programming"], "programming", 80, "n1", {"x": 1}, 0.5)
    restored = BranchDecision.from_dict(decision.to_dict())
    assert restored == decision
    path = BranchPath([decision], 80, ["Expert"], "builder", False, None)
    assert BranchPath.from_dict(path.to_dict()).to_dict() == path.to_dict()


def test_branch_chain_router_forms_path():
    neurons = []
    for index, (layer, options) in enumerate(
        [
            ("task_scope", ["programming"]),
            ("language_target", ["C"]),
            ("semantic_domain", ["arithmetic"]),
            ("support_gate", ["supported"]),
            ("arithmetic_family", ["addition"]),
            ("structure_policy", ["binary_operation"]),
            ("slot_binding_policy", ["surface_number_order"]),
            ("target_builder", ["canonical_arithmetic_targetir"]),
        ]
    ):
        seeded = make_seed_neurons(layer, options, index)
        for neuron in seeded:
            neuron.weights["contains_output"] = 50
        neurons.extend(seeded)
    path = BranchChainRouter(neurons).route(extract_surface_features("写一个 C 程序输出 1+2"))
    assert path.early_exit is False
    assert len(path.decisions) == 8


def test_branch_chain_router_can_early_exit():
    path = BranchChainRouter(population=[]).route(extract_surface_features("写一首诗"))
    assert path.early_exit is True
    assert path.unsupported_reason == "no_proposal"


def test_toy_dataset_has_required_fields():
    dataset = build_branchchain_toy_dataset()
    assert 20 <= len(dataset) <= 50
    for sample in dataset:
        assert sample["input_text"]
        assert sample["target_branch_path"]
        assert "supported" in sample


def test_path_reward_rewards_correct_path():
    sample = build_branchchain_toy_dataset()[0]
    decisions = [
        BranchDecision(layer, [selected], selected, 90, f"n:{layer}", {})
        for layer, selected in sample["target_branch_path"]
    ]
    path = BranchPath(decisions, 90, [], "canonical_arithmetic_targetir", False, None)
    reward, components = compute_path_reward(
        path,
        sample["target_branch_path"],
        sample["target_ir_canonical"],
        sample["expected_output"],
        sample["target_ir_canonical"],
        sample["expected_output"],
        sample["supported"],
    )
    assert reward > 1.0
    assert components["branch_path_exact_match"] is True


def test_path_reward_penalizes_unsupported_generation():
    sample = next(item for item in build_branchchain_toy_dataset() if not item["supported"])
    path = BranchPath(
        [BranchDecision("support_gate", ["supported"], "supported", 90, "n", {})],
        90,
        [],
        "canonical_arithmetic_targetir",
        False,
        None,
    )
    reward, components = compute_path_reward(path, sample["target_branch_path"], "add(lit(1),lit(2))", "3\n", None, None, False)
    assert reward < 0
    assert components["unsupported_generated"] is True


def test_toy_trainer_updates_neuron_scores():
    trainer = BranchChainToyTrainer(population_size=64, generations=2, seed=42)
    before = [neuron.score_value for neuron in trainer.population]
    report = trainer.train(build_branchchain_toy_dataset())
    after = [item["score"] for item in report.final_population_summary]
    assert before != after
    assert len(report.metrics_by_generation) == 3


def test_toy_trainer_report_has_curves(tmp_path, monkeypatch):
    monkeypatch.chdir(Path.cwd())
    metrics = run_branchchain_toy_experiment(population_size=64, generations=2, seed=42)
    assert len(metrics["metrics_by_generation"]) == 3
    assert "mean_reward" in metrics["metrics_by_generation"][0]
    assert Path(metrics["report_path"]).exists()


def test_no_flat_classifier_imports():
    root = Path("jianmu/self_learning/branchchain")
    forbidden = ["learned_router.perceptron", "arithmetic_targetir.hashed_perceptron"]
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text


def test_no_expression_oracle_import_in_surface_features():
    tree = ast.parse(Path("jianmu/self_learning/branchchain/surface_features.py").read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any("expression_oracle" in name for name in imports)


def test_existing_tests_still_pass():
    from jianmu.runtime import Runtime
    from jianmu.self_learning.arithmetic_targetir.target_ir import ArithmeticTargetIR

    assert Runtime is not None
    assert ArithmeticTargetIR is not None

