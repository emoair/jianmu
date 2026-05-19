import inspect
from collections import Counter, defaultdict

from jianmu.self_learning.branchchain import surface_features
from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.branchchain.toy_dataset import build_architecture_aligned_toy_dataset
from jianmu.self_learning.darwinforge import evolution
from jianmu.self_learning.darwinforge.evaluate import run_architecture_aligned_dataset_toy


def _target(sample, layer):
    for layer_name, selected in sample["target_branch_path"]:
        if layer_name == layer:
            return selected
    return None


def test_architecture_aligned_dataset_has_multiple_paraphrases_per_targetir():
    groups = defaultdict(list)
    for sample in build_architecture_aligned_toy_dataset():
        if sample["supported"]:
            groups[sample["target_ir_canonical"]].append(sample["input_text"])
    assert groups
    assert all(len(texts) >= 4 for texts in groups.values())


def test_no_supported_sample_uses_language_target_unknown():
    for sample in build_architecture_aligned_toy_dataset():
        if sample["supported"]:
            assert _target(sample, "language_target") != "unknown"


def test_implicit_c_samples_are_supported():
    samples = [s for s in build_architecture_aligned_toy_dataset() if _target(s, "language_target") == "implicit_C"]
    assert samples
    assert all(sample["supported"] for sample in samples)


def test_math_expression_samples_are_supported():
    samples = [sample for sample in build_architecture_aligned_toy_dataset() if sample["input_mode"] == "math_expression"]
    assert samples
    assert all(sample["supported"] for sample in samples)
    assert all(_target(sample, "language_target") == "math_expression_context" for sample in samples)


def test_ood_english_samples_are_not_positive_training_examples():
    samples = [s for s in build_architecture_aligned_toy_dataset() if s["input_mode"] == "ood_english"]
    assert samples
    assert all(not sample["supported"] for sample in samples)
    assert all(_target(sample, "language_target") == "reject_unsupported_language" for sample in samples)


def test_surface_features_include_chinese_and_english_ratios():
    zh = extract_surface_features("输出 1+2")
    en = extract_surface_features("calculate one plus two")
    assert "chinese_char_ratio" in zh
    assert "english_char_ratio" in en
    assert zh["contains_chinese_chars"] is True
    assert en["has_english_sentence"] is True


def test_surface_features_do_not_hardcode_english_rejection():
    features = extract_surface_features("calculate one plus two")
    assert "reject" not in features
    assert "unsupported" not in features


def test_early_reject_not_counted_as_true_missing_layer():
    metrics = run_architecture_aligned_dataset_toy(generations=1, population_per_layer=8, top_k_candidates=2, seed=7)
    final = metrics["new_metrics"]["metrics_by_generation"][-1]
    assert "true_missing_layer_rate" in final
    assert "early_reject_short_path_rate" in final
    assert final["true_missing_layer_rate"] <= final["missing_layer_rate"]


def test_report_contains_chinese_annotations():
    metrics = run_architecture_aligned_dataset_toy(generations=1, population_per_layer=8, top_k_candidates=2, seed=8)
    text = open(metrics["report_path"], encoding="utf-8").read()
    assert "Architecture-Aligned Dataset（架构对齐数据集）" in text
    assert "TargetIR（目标中间表示）" in text
    assert "OOD Evaluation（分布外评测）" in text


def test_no_expression_oracle_import_in_dataset_or_features():
    import jianmu.self_learning.branchchain.toy_dataset as toy_dataset

    combined = inspect.getsource(toy_dataset) + inspect.getsource(surface_features)
    assert "expression_oracle" not in combined
    assert "parse_controlled_expression" not in combined


def test_no_flat_classifier_imports():
    source = inspect.getsource(evolution)
    assert "learned_router.perceptron" not in source
    assert "arithmetic_targetir.hashed_perceptron" not in source


def test_existing_tests_still_pass():
    assert len(build_architecture_aligned_toy_dataset()) == 40
    counts = Counter(sample["input_mode"] for sample in build_architecture_aligned_toy_dataset())
    assert counts["zh_natural"] >= 8
    assert counts["math_expression"] >= 8
