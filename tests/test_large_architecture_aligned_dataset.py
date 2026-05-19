import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from jianmu.self_learning.datasets import large_architecture_aligned as dataset_alpha


@pytest.fixture()
def quick_dataset(tmp_path):
    out = tmp_path / "v0_6_8_quick"
    manifest = dataset_alpha.write_large_architecture_aligned_dataset(size=800, seed=42, out_dir=out)
    samples = dataset_alpha.load_jsonl(out / "jianmu_v0_6_8_all.jsonl")
    return out, manifest, samples


def _target(sample, layer):
    for layer_name, option in sample["target_branch_path"]:
        if layer_name == layer:
            return option
    return None


def test_generator_quick_mode_creates_files(quick_dataset):
    out, manifest, _ = quick_dataset
    assert manifest["actual_total"] > 0
    for name in [
        "train",
        "eval_seen_target_unseen_paraphrase",
        "eval_unseen_target",
        "eval_ood",
        "all",
    ]:
        assert (out / f"jianmu_v0_6_8_{name}.jsonl").exists()
    assert (out / "jianmu_v0_6_8_manifest.json").exists()
    assert (out / "jianmu_v0_6_8_report.md").exists()


def test_sample_schema_required_fields(quick_dataset):
    _, _, samples = quick_dataset
    required = {
        "sample_id",
        "input_text",
        "input_mode",
        "split",
        "paraphrase_group",
        "target_branch_path",
        "target_ir_canonical",
        "expected_output",
        "supported",
        "unsupported_reason",
        "expression_family",
        "structure_policy",
        "operator_count",
        "number_count",
        "has_parentheses",
        "uses_chinese_numerals",
        "contains_negative_number",
        "source_generator",
        "generator_seed",
    }
    assert required <= set(samples[0])


def test_sample_ids_unique(quick_dataset):
    _, _, samples = quick_dataset
    ids = [sample["sample_id"] for sample in samples]
    assert len(ids) == len(set(ids))


def test_input_text_no_duplicates(quick_dataset):
    _, _, samples = quick_dataset
    texts = [sample["input_text"] for sample in samples]
    assert len(texts) == len(set(texts))


def test_supported_samples_have_targetir_and_output(quick_dataset):
    _, _, samples = quick_dataset
    supported = [sample for sample in samples if sample["supported"]]
    assert supported
    assert all(sample["target_ir_canonical"] for sample in supported)
    assert all(sample["expected_output"] is not None for sample in supported)


def test_no_supported_sample_uses_language_target_unknown(quick_dataset):
    _, _, samples = quick_dataset
    assert not [sample for sample in samples if sample["supported"] and _target(sample, "language_target") == "unknown"]


def test_ood_english_not_supported(quick_dataset):
    _, _, samples = quick_dataset
    english = [sample for sample in samples if sample["input_mode"] == "ood_english"]
    assert english
    assert all(not sample["supported"] for sample in english)


def test_train_eval_unseen_target_no_group_leakage(quick_dataset):
    _, _, samples = quick_dataset
    train_groups = {s["paraphrase_group"] for s in samples if s["split"] == "train" and s["supported"]}
    unseen_groups = {s["paraphrase_group"] for s in samples if s["split"] == "eval_unseen_target" and s["supported"]}
    assert not train_groups & unseen_groups


def test_eval_seen_target_has_unseen_input_text(quick_dataset):
    _, _, samples = quick_dataset
    train_texts = {s["input_text"] for s in samples if s["split"] == "train"}
    seen_eval_texts = {s["input_text"] for s in samples if s["split"] == "eval_seen_target_unseen_paraphrase"}
    assert not train_texts & seen_eval_texts


def test_each_supported_group_has_multiple_paraphrases(quick_dataset):
    _, _, samples = quick_dataset
    groups = defaultdict(list)
    for sample in samples:
        if sample["supported"]:
            groups[sample["paraphrase_group"]].append(sample)
    assert groups
    assert min(len(rows) for rows in groups.values()) >= 4


def test_math_expression_language_target(quick_dataset):
    _, _, samples = quick_dataset
    math_samples = [sample for sample in samples if sample["input_mode"] == "math_expression"]
    assert math_samples
    assert all(_target(sample, "language_target") == "math_expression_context" for sample in math_samples)


def test_dataset_report_contains_chinese_annotations(quick_dataset):
    out, _, _ = quick_dataset
    report = (out / "jianmu_v0_6_8_report.md").read_text(encoding="utf-8")
    assert "Large Architecture-Aligned Dataset（大规模架构对齐数据集）" in report
    assert "Scale Smoke Benchmark（规模化冒烟基准）" in report
    assert "Dataset Leakage Check（数据泄漏检查）" in report


def test_validator_rejects_duplicate_input(quick_dataset):
    _, _, samples = quick_dataset
    bad = [dict(sample) for sample in samples[:2]]
    bad[1]["input_text"] = bad[0]["input_text"]
    quality = dataset_alpha.validate_large_dataset(bad)
    assert not quality["valid"]
    assert quality["duplicate_input_count"] == 1


def test_no_expression_oracle_import_in_dataset_generator():
    source = Path(dataset_alpha.__file__).read_text(encoding="utf-8")
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_external_api_calls():
    source = Path(dataset_alpha.__file__).read_text(encoding="utf-8")
    forbidden = ["requests.", "urllib.request", "openai", "anthropic", "httpx", "aiohttp"]
    assert not any(token in source for token in forbidden)

