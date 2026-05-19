from collections import defaultdict
from pathlib import Path

import pytest

from jianmu.self_learning.datasets.symbol_grounding import (
    load_jsonl,
    write_symbol_grounding_dataset,
)


@pytest.fixture()
def quick_symbol_dataset(tmp_path):
    out = tmp_path / "v0_7_0_quick"
    manifest = write_symbol_grounding_dataset(size=600, seed=42, out_dir=out)
    samples = load_jsonl(out / "jianmu_v0_7_0_symbol_grounding_all.jsonl")
    return out, manifest, samples


def test_symbol_grounding_dataset_quick_generation(quick_symbol_dataset):
    out, manifest, samples = quick_symbol_dataset
    assert manifest["actual_total"] == 600
    assert (out / "jianmu_v0_7_0_symbol_grounding_train.jsonl").exists()
    assert samples


def test_symbol_grounding_schema_required_fields(quick_symbol_dataset):
    _, _, samples = quick_symbol_dataset
    required = {
        "sample_id",
        "input_text",
        "split",
        "curriculum_stage",
        "input_mode",
        "paraphrase_group",
        "paired_group_id",
        "target_branch_path",
        "target_ir_canonical",
        "expected_output",
        "supported",
        "unsupported_reason",
        "symbol_slots",
        "operator_slots",
        "expression_family",
        "structure_policy",
        "source_generator",
        "generator_seed",
    }
    assert required <= set(samples[0])


def test_paired_group_contains_arabic_and_zh_forms(quick_symbol_dataset):
    _, _, samples = quick_symbol_dataset
    groups = defaultdict(set)
    for sample in samples:
        if sample["supported"]:
            groups[sample["paired_group_id"]].add(sample["input_mode"])
    assert any({"arabic_math_expression", "zh_number_expression"} <= modes for modes in groups.values())


def test_symbol_slots_present_for_zh_number_expression(quick_symbol_dataset):
    _, _, samples = quick_symbol_dataset
    zh = [sample for sample in samples if sample["input_mode"] == "zh_number_expression" and sample["supported"]]
    assert zh
    assert all(sample["symbol_slots"] for sample in zh)


def test_operator_slots_present_for_operator_grounding(quick_symbol_dataset):
    _, _, samples = quick_symbol_dataset
    rows = [sample for sample in samples if sample["curriculum_stage"] == "operator_grounding" and sample["supported"]]
    assert rows
    assert all(sample["operator_slots"] for sample in rows)


def test_report_contains_chinese_annotations(quick_symbol_dataset):
    out, _, _ = quick_symbol_dataset
    report = (out / "jianmu_v0_7_0_symbol_grounding_report.md").read_text(encoding="utf-8")
    assert "Symbol Grounding Curriculum（符号接地课程）" in report
    assert "Raw Symbol Feature（原始符号特征）" in report


def test_no_expression_oracle_import_in_symbol_grounding():
    source = Path("jianmu/self_learning/datasets/symbol_grounding.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_external_api_calls():
    source = Path("jianmu/self_learning/datasets/symbol_grounding.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "urllib.request", "openai", "anthropic", "httpx", "aiohttp"]
    assert not any(token in source for token in forbidden)

