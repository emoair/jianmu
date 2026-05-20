import json
import subprocess
import sys
from pathlib import Path

from jianmu.self_learning.darwinforge.canonicalized_training_probe import (
    CanonicalizedTrainingConfig,
    compare_raw_and_canonical,
)
from jianmu.self_learning.datasets.symbol_grounding import build_symbol_grounding_dataset, write_symbol_grounding_dataset


REPO_ROOT = Path(__file__).resolve().parents[1]


def _splits():
    return build_symbol_grounding_dataset(size=120, seed=13)


def test_probe_compare_both_runs():
    splits = _splits()
    raw_config = CanonicalizedTrainingConfig.for_mode("quick", canonicalization_enabled=False, population_per_layer=4, generations=1, top_k=2, train_limit=40, eval_limit=30, ood_limit=20)
    can_config = CanonicalizedTrainingConfig.for_mode("quick", canonicalization_enabled=True, population_per_layer=4, generations=1, top_k=2, train_limit=40, eval_limit=30, ood_limit=20)
    metrics = compare_raw_and_canonical(splits["train"], splits["eval"], splits["ood"], raw_config, can_config)
    assert "raw_training" in metrics
    assert "canonical_training" in metrics
    assert "delta" in metrics


def test_report_contains_raw_vs_canonical_delta(tmp_path):
    dataset_dir = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=120, seed=17, out_dir=dataset_dir)
    records_dir = tmp_path / "records"
    subprocess.run(
        [
            sys.executable,
            "examples/run_canonicalized_training_probe.py",
            "--mode",
            "quick",
            "--compare",
            "both",
            "--dataset-dir",
            str(dataset_dir),
            "--population-per-layer",
            "4",
            "--generations",
            "1",
            "--top-k",
            "2",
            "--records-dir",
            str(records_dir),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    report = (records_dir / "canonicalized_training_report.md").read_text(encoding="utf-8")
    assert "raw_vs_canonical_delta（原始与规范差值）" in report
    assert "Canonicalized Training Probe（规范化输入训练探针）" in report


def test_report_contains_chinese_annotations(tmp_path):
    dataset_dir = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=120, seed=19, out_dir=dataset_dir)
    records_dir = tmp_path / "records"
    subprocess.run(
        [
            sys.executable,
            "examples/run_canonicalized_training_probe.py",
            "--mode",
            "quick",
            "--compare",
            "both",
            "--dataset-dir",
            str(dataset_dir),
            "--population-per-layer",
            "4",
            "--generations",
            "1",
            "--top-k",
            "2",
            "--records-dir",
            str(records_dir),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    report = (records_dir / "canonicalized_training_report.md").read_text(encoding="utf-8")
    assert "Raw Input Training（原始输入训练）" in report
    assert "Canonical Input Training（规范输入训练）" in report
    assert "OOD" in report and "分布外" in report


def test_probe_writes_examples(tmp_path):
    dataset_dir = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=120, seed=23, out_dir=dataset_dir)
    records_dir = tmp_path / "records"
    subprocess.run(
        [
            sys.executable,
            "examples/run_canonicalized_training_probe.py",
            "--mode",
            "quick",
            "--compare",
            "both",
            "--dataset-dir",
            str(dataset_dir),
            "--population-per-layer",
            "4",
            "--generations",
            "1",
            "--top-k",
            "2",
            "--records-dir",
            str(records_dir),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    examples = json.loads((records_dir / "canonicalized_training_examples.json").read_text(encoding="utf-8"))
    assert isinstance(examples, list)


def test_no_expression_oracle_import_in_canonicalized_training():
    import inspect
    import jianmu.self_learning.darwinforge.canonicalized_training_probe as module

    assert "expression_oracle" not in inspect.getsource(module)


def test_no_external_api_calls():
    import inspect
    import jianmu.self_learning.darwinforge.canonicalized_training_probe as module
    import examples.run_canonicalized_training_probe as script

    source = inspect.getsource(module) + inspect.getsource(script)
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source.lower()


def test_no_flat_classifier_imports():
    import inspect
    import jianmu.self_learning.darwinforge.canonicalized_training_probe as module

    source = inspect.getsource(module)
    assert "learned_router.perceptron" not in source
    assert "arithmetic_targetir.hashed_perceptron" not in source

