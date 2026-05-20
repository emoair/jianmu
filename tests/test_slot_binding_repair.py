from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.slot_binding_repair import apply_slot_binding_repair


def _sample(option="surface_number_order", text="1+2"):
    return {
        "sample_id": f"s-{option}",
        "split": "train",
        "input_text": text,
        "input_mode": "arabic_math_expression",
        "target_branch_path": [["slot_binding_policy", option]],
        "supported": True,
        "number_count": 2,
        "operator_count": 1,
        "structure_policy": "binary_operation",
    }


def test_slot_binding_repair_improves_surface_number_order_score():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)
    before = [{"score_diagnostic": {"layers": [{"layer_name": "slot_binding_policy", "target_option_rank": 4, "target_option_score": 3}]}}]

    metrics = apply_slot_binding_repair(population, [_sample()], before)

    assert metrics["slot_binding_correct_score_after"] >= metrics["slot_binding_correct_score_before"]


def test_slot_binding_repair_handles_signed_number_order():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=43)

    metrics = apply_slot_binding_repair(population, [_sample("signed_number_order", "-6")], [])

    assert metrics["slot_binding_update_distribution"].get("signed_number_order", 0) > 0


def test_slot_binding_repair_does_not_force_chinese_order_after_canonicalization():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=44)
    sample = _sample("chinese_number_order", "三加四")
    sample["input_mode"] = "zh_number_expression"

    metrics = apply_slot_binding_repair(population, [sample], [])

    assert metrics["slot_binding_update_distribution"].get("surface_number_order", 0) > 0
