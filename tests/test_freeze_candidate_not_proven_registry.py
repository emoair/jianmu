from jianmu.self_learning.darwinforge.freeze_candidate_not_proven_registry import (
    REQUIRED_NOT_PROVEN,
    run_not_proven_registry,
)


def test_not_proven_registry_contains_required_items(tmp_path):
    registry = run_not_proven_registry(tmp_path)
    names = {row["claim"] for row in registry["not_proven"]}
    assert set(REQUIRED_NOT_PROVEN).issubset(names)
    assert "natural language layer completed" in names
