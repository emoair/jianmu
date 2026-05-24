import json

from jianmu.self_learning.darwinforge.arithmetic_dataset_audit import audit_arithmetic_dataset


def _write_row(root, row):
    split_dir = root / row["split"]
    split_dir.mkdir(parents=True, exist_ok=True)
    (split_dir / f"{row['split']}_000.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    for split in ["train", "eval", "test", "heldout"]:
        (root / split).mkdir(exist_ok=True)


def _base_row():
    return {
        "id": "x",
        "dataset_version": "v0.9.2",
        "split": "train",
        "stage": "single_op",
        "category": "current_supported_arithmetic",
        "input": "1+2",
        "canonical_expression": "1+2",
        "target_ir": {"op": "add", "args": [{"op": "int", "value": 1}, {"op": "int", "value": 2}]},
        "expected_output": "3\n",
        "expected_type": "int",
        "boundary_label": "current_supported",
        "expected_action": "accept_supported",
        "nutrient_policy": {},
        "toxicity_policy": {},
        "operator_set": ["add"],
        "operator_count": 1,
        "integer_range": [-999, 999],
        "has_parentheses": False,
        "has_unary_minus": False,
        "has_division": False,
        "division_kind": "none",
        "expression_depth": 2,
        "result_abs": 3,
        "template_id": "t",
        "expression_group_id": "eg",
        "paraphrase_group_id": "pg",
        "target_group_id": "tg",
        "leakage_guard": {"free_inference_forbidden_fields": [], "non_supported_has_target": False},
        "provenance": {},
    }


def test_dataset_audit_blocks_leakage(tmp_path):
    row = _base_row()
    _write_row(tmp_path, row)
    eval_row = dict(row, id="y", split="eval")
    _write_row(tmp_path, eval_row)
    audit = audit_arithmetic_dataset(tmp_path)
    assert audit["train_eval_input_leakage_count"] == 1
    assert audit["audit_passed"] is False


def test_dataset_audit_blocks_answer_in_input(tmp_path):
    row = _base_row()
    row["input"] = "1+2 answer is 3"
    _write_row(tmp_path, row)
    audit = audit_arithmetic_dataset(tmp_path)
    assert audit["input_contains_expected_output_count"] == 1
