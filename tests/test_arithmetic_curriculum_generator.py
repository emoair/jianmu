from pathlib import Path

from jianmu.self_learning.darwinforge.arithmetic_curriculum_generator import generate_scale


def test_non_supported_has_no_targetir(tmp_path):
    summary = generate_scale("small", tmp_path / "small", seed=3, shard_size=1000)
    audit = summary["audit"]
    assert audit["non_supported_has_targetir_count"] == 0
    assert audit["non_supported_has_expected_output_count"] == 0


def test_supported_has_expected_output(tmp_path):
    summary = generate_scale("small", tmp_path / "small", seed=4, shard_size=1000)
    audit = summary["audit"]
    assert audit["supported_missing_targetir_count"] == 0
    assert audit["supported_missing_expected_output_count"] == 0


def test_dataset_generator_no_duplicate_inputs(tmp_path):
    summary = generate_scale("small", tmp_path / "small", seed=5, shard_size=1000)
    assert summary["audit"]["duplicate_input_count"] == 0


def test_dataset_generator_split_leakage_guard(tmp_path):
    summary = generate_scale("small", tmp_path / "small", seed=6, shard_size=1000)
    assert summary["audit"]["train_eval_input_leakage_count"] == 0
    assert summary["audit"]["expression_group_leakage_count"] == 0


def test_no_expression_oracle_import():
    files = list(Path("jianmu/self_learning/darwinforge").glob("arithmetic_*.py"))
    assert files
    assert "import expression_oracle" not in "\n".join(path.read_text(encoding="utf-8") for path in files)


def test_no_external_api_calls():
    files = list(Path("jianmu/self_learning/darwinforge").glob("arithmetic_*.py"))
    text = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "requests." not in text
    assert "openai" not in text.lower()
