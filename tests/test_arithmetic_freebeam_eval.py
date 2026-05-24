from jianmu.self_learning.darwinforge.arithmetic_freebeam_eval import FORBIDDEN_FIELDS, allowed_view, evaluate_arithmetic_freebeam


def _supported(i: int = 1):
    return {
        "id": f"s{i}",
        "category": "current_supported_arithmetic",
        "input": f"{i}+1",
        "canonical_expression": f"{i}+1",
        "expected_output": f"{i + 1}\n",
        "target_ir": {"op": "add", "args": [{"op": "int", "value": i}, {"op": "int", "value": 1}]},
        "boundary_label": "current_supported",
        "expected_action": "accept_supported",
        "nutrient_policy": {"positive": ["correct_accept"]},
        "toxicity_policy": {"toxic": ["false_reject"]},
    }


def test_arithmetic_freebeam_eval_forbidden_fields():
    view = allowed_view(_supported())
    assert not (FORBIDDEN_FIELDS & set(view))
    metrics = evaluate_arithmetic_freebeam([_supported(1), _supported(2)], learned_strength=1.0)
    assert metrics["forbidden_field_access_count"] == 0
    assert metrics["supported_candidate_in_beam_rate"] > 0


def test_arithmetic_training_does_not_read_target_fields_in_free_eval():
    row = _supported()
    stripped = allowed_view(row)
    row["expected_output"] = "999\n"
    metrics = evaluate_arithmetic_freebeam([{**row, **stripped}], learned_strength=1.0)
    assert metrics["freebeam_eval_sample_count"] == 1
    assert metrics["forbidden_field_access_count"] == 0
