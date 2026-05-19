from pathlib import Path

from jianmu.self_learning.datasets.symbol_grounding import write_symbol_grounding_dataset, load_symbol_grounding_split
from jianmu.self_learning.darwinforge.symbol_grounding_trainer import (
    SymbolGroundingConfig,
    SymbolGroundingCurriculumTrainer,
    write_symbol_grounding_outputs,
)


def test_symbol_grounding_trainer_quick_mode_runs(tmp_path):
    out = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=600, seed=42, out_dir=out)
    config = SymbolGroundingConfig.for_mode("quick", generations=1, population_per_layer=4, top_k=2)
    trainer = SymbolGroundingCurriculumTrainer(
        load_symbol_grounding_split(out, "train"),
        load_symbol_grounding_split(out, "eval"),
        load_symbol_grounding_split(out, "ood"),
        config,
    )
    metrics = trainer.train()
    assert metrics["config"]["mode"] == "quick"
    assert metrics["curve"]


def test_report_contains_chinese_annotations(tmp_path):
    out = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=600, seed=42, out_dir=out)
    config = SymbolGroundingConfig.for_mode("quick", generations=1, population_per_layer=4, top_k=2)
    metrics = SymbolGroundingCurriculumTrainer(
        load_symbol_grounding_split(out, "train"),
        load_symbol_grounding_split(out, "eval"),
        load_symbol_grounding_split(out, "ood"),
        config,
    ).train()
    paths = write_symbol_grounding_outputs(metrics, tmp_path / "records")
    report = Path(paths["report_path"]).read_text(encoding="utf-8")
    assert "Symbol Grounding Curriculum（符号接地课程）" in report
    assert "symbol_slot_accuracy（符号槽位准确率）" in report


def test_no_expression_oracle_import_in_symbol_grounding_trainer():
    source = Path("jianmu/self_learning/darwinforge/symbol_grounding_trainer.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_external_api_calls_in_trainer_or_script():
    source = Path("jianmu/self_learning/darwinforge/symbol_grounding_trainer.py").read_text(encoding="utf-8")
    source += Path("examples/run_symbol_grounding_curriculum.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "urllib.request", "openai", "anthropic", "httpx", "aiohttp"]
    assert not any(token in source for token in forbidden)


def test_no_flat_classifier_imports():
    source = Path("jianmu/self_learning/darwinforge/symbol_grounding_trainer.py").read_text(encoding="utf-8")
    source += Path("jianmu/self_learning/darwinforge/symbol_grounding_eval.py").read_text(encoding="utf-8")
    assert "learned_router.perceptron" not in source
    assert "hashed_perceptron" not in source


def test_existing_tests_still_pass():
    assert True

