from types import SimpleNamespace

from jianmu.self_learning.darwinforge.annealed_pruning import annealing_schedule
from jianmu.self_learning.darwinforge.rootforge import nutrient_contrast


def test_annealing_reduces_beam_and_perturbation():
    early = annealing_schedule(0, 10, base_beam_size=40, base_perturbation_scale=0.2)
    late = annealing_schedule(9, 10, base_beam_size=40, base_perturbation_scale=0.2)

    assert early.effective_beam_size > late.effective_beam_size
    assert early.effective_perturbation_scale > late.effective_perturbation_scale
    assert early.pruning_strength < late.pruning_strength


def test_nutrient_contrast_positive_beats_negative_margin():
    positive = SimpleNamespace(root_id="p", nutrient_score=5.0)
    negative = SimpleNamespace(root_id="n", nutrient_score=1.0)

    event = nutrient_contrast(positive, negative, margin=1.0)

    assert event["satisfied"] is True
    assert event["positive_score"] > event["negative_score"]
