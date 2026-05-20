from jianmu.self_learning.darwinforge.nutrient_zone import create_zones_from_rescued_paths


def _rescued(sample_id, mode="arabic_math_expression"):
    return {
        "sample_id": sample_id,
        "split": "train",
        "rescued_by_subbeam": True,
        "fork_layer": "slot_binding_policy",
        "input_mode": mode,
        "expression_family": "addition",
        "structure_policy": "binary_operation",
        "number_count": 2,
        "operator_count": 1,
        "subbeam_path": [["task_scope", "programming"], ["slot_binding_policy", "surface_number_order"]],
        "rescued_target_ir": "add(lit(1),lit(2))",
    }


def test_create_nutrient_zones_groups_by_fork_and_features():
    zones = create_zones_from_rescued_paths([_rescued("a"), _rescued("b")], [])

    assert len(zones) == 1
    assert zones[0].fork_layer == "slot_binding_policy"
    assert len(zones[0].source_sample_ids) == 2


def test_nutrient_zone_does_not_use_targetir_as_feature():
    zones = create_zones_from_rescued_paths([_rescued("a"), _rescued("b")], [])

    assert "target_ir" not in str(zones[0].feature_pattern)
