from types import SimpleNamespace

from jianmu.self_learning.darwinforge.root_necrosis import NecrosisQueue


def test_necrosis_marks_persistent_high_score_wrong():
    root = SimpleNamespace(root_id="r", sample_id="s", root_type="high_score_wrong", nutrient_score=0.0, necrosis_state=None)
    queue = NecrosisQueue(no_nutrient_generations=2)

    first = queue.observe(root, generation=0, phase="early")
    second = queue.observe(root, generation=1, phase="middle")

    assert first.action == "queued"
    assert second.action == "decayed"
    assert queue.summary()["high_score_wrong_necrosis_count"] == 2


def test_necrosis_prunes_in_late_phase():
    root = SimpleNamespace(root_id="r", sample_id="s", root_type="high_score_wrong", nutrient_score=0.0, necrosis_state=None)
    queue = NecrosisQueue(no_nutrient_generations=1)

    event = queue.observe(root, generation=3, phase="late")

    assert event.action == "pruned"
    assert queue.summary()["necrosis_pruned_count"] == 1
