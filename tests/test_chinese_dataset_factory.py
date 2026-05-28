from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.chinese_dataset_audit import audit_chinese_dataset, audit_rows
from jianmu.self_learning.darwinforge.chinese_dataset_compiler_audit import run_chinese_dataset_compiler_audit
from jianmu.self_learning.darwinforge.chinese_dataset_factory import generate_codex_grammar_chinese_dataset, make_sample
from jianmu.self_learning.darwinforge.chinese_dataset_readiness import write_chinese_dataset_readiness
from jianmu.self_learning.darwinforge.chinese_program_description_grammar import detect_input_language, has_chinese


def test_chinese_supported_samples_are_chinese() -> None:
    row = make_sample(1, "pilot", "current_supported_bounded_substrate_zh")
    assert row["support_status"] == "current_supported"
    assert row["input_language"] == "zh"
    assert has_chinese(row["input"])
    assert all(detect_input_language(v) == "zh" for v in row["natural_language_variants"])


def test_english_not_current_supported() -> None:
    row = make_sample(2, "pilot", "english_unrelated_request")
    assert row["input_language"] == "en"
    assert row["support_status"] != "current_supported"
    assert row["expected_action"] != "train_current"


def test_mixed_language_not_current_supported() -> None:
    row = make_sample(3, "pilot", "mixed_language_boundary")
    assert row["input_language"] == "mixed"
    assert row["support_status"] != "current_supported"


def test_chinese_program_description_grammar() -> None:
    assert detect_input_language("声明变量并计算") == "zh"
    assert detect_input_language("compute value") == "en"
    assert detect_input_language("请 compute value") == "mixed"


def test_chinese_bounded_control_generator() -> None:
    row = make_sample(4, "pilot", "bounded_control_hard_supported_zh")
    assert row["target_ir"]["op"] == "Program"
    assert "printf" not in json.dumps(row["target_ir"])


def test_chinese_dataset_audit_blocks_language_leakage() -> None:
    row = make_sample(5, "pilot", "current_supported_bounded_substrate_zh")
    row["input_language"] = "en"
    audit = audit_rows([row])
    assert audit["current_supported_non_chinese_count"] == 1
    assert audit["audit_passed"] is False


def test_chinese_dataset_audit_blocks_future_targets() -> None:
    row = make_sample(6, "pilot", "near_supported_pure_function_zh")
    row["target_ir"] = {"op": "Program"}
    audit = audit_rows([row])
    assert audit["non_supported_has_targetir_count"] == 1


def test_chinese_dataset_compiler_audit_uses_real_cl(tmp_path: Path) -> None:
    generate_codex_grammar_chinese_dataset(tmp_path / "data", tmp_path / "records", ["pilot"], seed=98)
    metrics = run_chinese_dataset_compiler_audit(tmp_path / "data", tmp_path / "records2", supported_spot=2, boundary_spot=2, compile_worker_count=1, seed=98)
    assert metrics["backend_type"] == "real_c_compiler"
    assert metrics["compiler_name"] == "cl"


def test_chinese_dataset_compiler_audit_blocks_english_compile(tmp_path: Path) -> None:
    generate_codex_grammar_chinese_dataset(tmp_path / "data", tmp_path / "records", ["pilot"], seed=98)
    metrics = run_chinese_dataset_compiler_audit(tmp_path / "data", tmp_path / "records2", supported_spot=2, boundary_spot=20, compile_worker_count=1, seed=98)
    assert metrics["english_compiled_count"] == 0
    assert metrics["mixed_language_compiled_count"] == 0


def test_comparison_vs_raw_generation(tmp_path: Path) -> None:
    generate_codex_grammar_chinese_dataset(tmp_path / "data", tmp_path / "records", ["pilot"], seed=98)
    audit = audit_chinese_dataset(tmp_path / "data", tmp_path / "records")
    compiler = run_chinese_dataset_compiler_audit(tmp_path / "data", tmp_path / "records", supported_spot=2, boundary_spot=2, compile_worker_count=1, seed=98)
    readiness = write_chinese_dataset_readiness(tmp_path / "records", audit, compiler)
    comparison = json.loads((tmp_path / "records" / "comparison_vs_raw_generation.json").read_text())
    assert comparison["raw_llm_free_generation_should_be_discontinued"] is True
    assert readiness["codex_grammar_outperforms_raw_llm_generation"] is True


def test_chinese_dataset_readiness_no_turing_claim(tmp_path: Path) -> None:
    generate_codex_grammar_chinese_dataset(tmp_path / "data", tmp_path / "records", ["pilot"], seed=98)
    audit = audit_chinese_dataset(tmp_path / "data", tmp_path / "records")
    compiler = run_chinese_dataset_compiler_audit(tmp_path / "data", tmp_path / "records", supported_spot=1, boundary_spot=1, compile_worker_count=1, seed=98)
    write_chinese_dataset_readiness(tmp_path / "records", audit, compiler)
    text = (tmp_path / "records" / "mainline_conclusion.md").read_text()
    assert "Turing completeness" in text
    assert "solved program synthesis" in text


def test_no_expression_oracle_import() -> None:
    text = "\n".join(Path("jianmu/self_learning/darwinforge").glob("chinese_*.py").__str__() for _ in [])
    for path in Path("jianmu/self_learning/darwinforge").glob("chinese_*.py"):
        assert "expression_oracle" not in path.read_text(encoding="utf-8")


def test_no_external_api_calls() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("chinese_*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "requests." not in text
        assert "urllib" not in text
        assert "openai" not in text


def test_no_hardcoded_keyword_gate() -> None:
    for path in Path("jianmu/self_learning/darwinforge").glob("chinese_*.py"):
        assert "keyword gate" not in path.read_text(encoding="utf-8").lower()


def test_real_promotion_disabled() -> None:
    row = make_sample(1, "pilot", "current_supported_bounded_substrate_zh")
    assert row["provenance"]["external_api_used"] is False
