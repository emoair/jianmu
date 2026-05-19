import json
import subprocess
import sys
from pathlib import Path

from jianmu.self_learning.datasets.symbol_grounding import build_symbol_grounding_dataset, write_symbol_grounding_dataset
from jianmu.self_learning.darwinforge.canonical_symbol_eval import compare_canonical_symbol_layer, evaluate_canonical_symbol_layer
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


REPO_ROOT = Path(__file__).resolve().parents[1]


def _quick_samples():
    splits = build_symbol_grounding_dataset(size=120, seed=7)
    return splits["train"] + splits["eval"] + splits["ood"]


def test_probe_runs_with_canonicalization_off():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=1)
    metrics = evaluate_canonical_symbol_layer(population, _quick_samples()[:40], top_k=2, canonicalization_enabled=False)
    assert "overall" in metrics
    assert "zh_number_metrics" in metrics


def test_probe_runs_with_canonicalization_on():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=1)
    metrics = evaluate_canonical_symbol_layer(population, _quick_samples()[:40], top_k=2, canonicalization_enabled=True)
    assert "canonical_metrics" in metrics
    assert metrics["canonical_metrics"]["canonicalization_success_rate"] >= 0.0


def test_probe_reports_on_off_delta():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=1)
    metrics = compare_canonical_symbol_layer(population, _quick_samples()[:40], top_k=2)
    assert "without_canonicalization" in metrics
    assert "with_canonicalization" in metrics
    assert "raw_vs_canonical_targetir_gap" in metrics["delta"]


def test_zh_number_false_reject_improves_or_is_reported():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=1)
    metrics = compare_canonical_symbol_layer(population, _quick_samples()[:40], top_k=2)
    assert "zh_number_expression_false_reject_rate" in metrics["without_canonicalization"]["zh_number_metrics"]
    assert "zh_number_expression_false_reject_rate" in metrics["with_canonicalization"]["zh_number_metrics"]


def test_report_contains_chinese_annotations(tmp_path):
    dataset_dir = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=120, seed=3, out_dir=dataset_dir)
    records_dir = tmp_path / "records"
    subprocess.run(
        [
            sys.executable,
            "examples/run_canonical_symbol_layer_probe.py",
            "--dataset",
            str(dataset_dir / "jianmu_v0_7_0_symbol_grounding_all.jsonl"),
            "--canonicalization",
            "both",
            "--sample-size",
            "40",
            "--population-per-layer",
            "4",
            "--top-k",
            "2",
            "--records-dir",
            str(records_dir),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    report = (records_dir / "canonical_symbol_report.md").read_text(encoding="utf-8")
    assert "Canonical Symbol Layer（规范符号层）" in report
    assert "Source Map（源映射）" in report
    assert "OOD Evaluation（分布外评测）" in report


def test_probe_writes_examples(tmp_path):
    dataset_dir = tmp_path / "dataset"
    write_symbol_grounding_dataset(size=120, seed=5, out_dir=dataset_dir)
    records_dir = tmp_path / "records"
    subprocess.run(
        [
            sys.executable,
            "examples/run_canonical_symbol_layer_probe.py",
            "--dataset",
            str(dataset_dir / "jianmu_v0_7_0_symbol_grounding_all.jsonl"),
            "--canonicalization",
            "both",
            "--sample-size",
            "40",
            "--population-per-layer",
            "4",
            "--top-k",
            "2",
            "--records-dir",
            str(records_dir),
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    examples = json.loads((records_dir / "canonical_symbol_examples.json").read_text(encoding="utf-8"))
    assert any(row["input_text"] == "三加四" and row["canonical_text"] == "3+4" for row in examples)
