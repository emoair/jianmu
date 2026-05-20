from types import SimpleNamespace

from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.darwinforge.root_regrowth import choose_regrowth_fork_point, find_stable_prefix, plan_regrowth


def _path():
    return BranchPath(
        decisions=[
            BranchDecision("task_scope", ["programming"], "programming", 80, "n0", {}),
            BranchDecision("language_target", ["math_expression_context"], "math_expression_context", 75, "n1", {}),
            BranchDecision("semantic_domain", ["arithmetic"], "arithmetic", 30, "n2", {}),
        ]
    )


def test_regrowth_finds_stable_prefix():
    root = SimpleNamespace(stable_prefix=[["task_scope", "programming"], ["language_target", "math_expression_context"]], branch_path=_path())

    assert find_stable_prefix(root) == root.stable_prefix


def test_regrowth_forks_after_confidence_collapse():
    root = SimpleNamespace(
        root_id="r",
        sample_id="s",
        stable_prefix=[["task_scope", "programming"]],
        first_confidence_collapse_layer="semantic_domain",
        first_wrong_layer=None,
        branch_path=_path(),
    )

    assert choose_regrowth_fork_point(root) == "language_target"


def test_regrowth_event_serialization():
    root = SimpleNamespace(
        root_id="r",
        sample_id="s",
        stable_prefix=[["task_scope", "programming"]],
        first_confidence_collapse_layer="semantic_domain",
        first_wrong_layer=None,
        branch_path=_path(),
    )

    event = plan_regrowth(root, 2, ["task_scope", "language_target", "semantic_domain"], window=1)

    assert event.regrowth_fork_point == "language_target"
    assert event.created_clone_layers == ["semantic_domain"]
    assert event.to_dict()["generation"] == 2
