import json
from collections import Counter
from pathlib import Path

from jianmu.self_learning.dataset_alpha import (
    EVAL_COUNT,
    FAMILY_COUNTS,
    SEED,
    TRAIN_COUNT,
    build_dataset,
    write_dataset_files,
)


DATASET_DIR = Path("datasets") / "v0_5_6"


def test_dataset_alpha_generates_1000_samples():
    samples = build_dataset(seed=SEED)
    assert len(samples) == 1000
    assert Counter(sample["task_family"] for sample in samples) == FAMILY_COUNTS


def test_dataset_alpha_reproducible_with_seed(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    write_dataset_files(first_dir, seed=SEED)
    write_dataset_files(second_dir, seed=SEED)
    assert (first_dir / "jianmu_zh_intent_1000.jsonl").read_bytes() == (
        second_dir / "jianmu_zh_intent_1000.jsonl"
    ).read_bytes()


def test_dataset_alpha_train_eval_split():
    samples = build_dataset(seed=SEED)
    split_counts = Counter(sample["split"] for sample in samples)
    assert split_counts["train"] == TRAIN_COUNT
    assert split_counts["eval"] == EVAL_COUNT


def test_dataset_alpha_required_fields_present():
    required = {
        "sample_id",
        "split",
        "input_text",
        "language",
        "task_family",
        "intent",
        "slots",
        "route_id",
        "atomic_experts",
        "program_ir_tokens",
        "expected_output",
        "expected_output_provenance",
        "supported",
        "unsupported_reason",
        "difficulty",
        "template_id",
        "paraphrase_group",
        "metadata",
    }
    for sample in build_dataset(seed=SEED):
        assert required <= set(sample)
        assert sample["language"] == "zh-CN"


def test_dataset_alpha_expected_output_ground_truth():
    for sample in build_dataset(seed=SEED):
        if sample["supported"]:
            assert sample["expected_output"] == f"{sum(sample['slots']['values'])}\n"
            assert sample["expected_output_provenance"] != "none"
        else:
            assert sample["expected_output"] is None


def test_dataset_alpha_unsupported_has_no_ir_tokens():
    for sample in build_dataset(seed=SEED):
        if not sample["supported"]:
            assert sample["atomic_experts"] == []
            assert sample["program_ir_tokens"] == []


def test_dataset_alpha_no_duplicate_input_between_train_eval():
    samples = build_dataset(seed=SEED)
    train_inputs = {sample["input_text"] for sample in samples if sample["split"] == "train"}
    eval_inputs = {sample["input_text"] for sample in samples if sample["split"] == "eval"}
    assert train_inputs.isdisjoint(eval_inputs)
    assert len(train_inputs) + len(eval_inputs) == len(samples)


def test_dataset_alpha_eval_has_eval_only_templates():
    eval_samples = [sample for sample in build_dataset(seed=SEED) if sample["split"] == "eval"]
    eval_only = [sample for sample in eval_samples if sample["template_id"].startswith("eval_only_")]
    assert len(eval_only) >= 50


def test_dataset_alpha_eval_has_unseen_number_combinations():
    samples = build_dataset(seed=SEED)
    train_signatures = {_number_signature(sample) for sample in samples if sample["split"] == "train"}
    unseen_eval = [
        sample for sample in samples
        if sample["split"] == "eval" and _number_signature(sample) not in train_signatures
    ]
    assert len(unseen_eval) >= 30


def test_dataset_alpha_contains_chinese_numbers_and_negatives():
    samples = build_dataset(seed=SEED)
    assert any(sample["metadata"]["contains_chinese_numbers"] for sample in samples)
    assert any(sample["metadata"]["contains_negative_numbers"] for sample in samples)
    eval_samples = [sample for sample in samples if sample["split"] == "eval"]
    assert any(sample["metadata"]["contains_chinese_numbers"] for sample in eval_samples)
    assert any(sample["metadata"]["contains_negative_numbers"] for sample in eval_samples)
    assert any(sample["task_family"] == "no_op_keep_existing" for sample in eval_samples)
    assert any(not sample["supported"] for sample in eval_samples)
    assert any(sample["task_family"] == "explicit_expression_rewrite" for sample in eval_samples)
    assert any(sample["task_family"] == "comparison_prealpha" for sample in eval_samples)


def test_dataset_alpha_report_exists():
    report = DATASET_DIR / "jianmu_zh_intent_1000_report.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "total samples: 1000" in text
    assert "This dataset does not prove learned routing." in text


def test_dataset_alpha_files_match_generator():
    path = DATASET_DIR / "jianmu_zh_intent_1000.jsonl"
    file_samples = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert file_samples == build_dataset(seed=SEED)


def _number_signature(sample):
    slots = sample["slots"]
    if "left_values" in slots or "right_values" in slots:
        return tuple(slots.get("left_values", [])), tuple(slots.get("right_values", []))
    return tuple(slots.get("values") or [])
