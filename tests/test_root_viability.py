from types import SimpleNamespace

from jianmu.self_learning.darwinforge.root_viability import diagnose_root_viability, summarize_viability


def _root(**overrides):
    base = dict(
        root_id="r",
        rank=3,
        target_ir_exact_match=True,
        stable_prefix=[["task_scope", "programming"], ["language_target", "math_expression_context"], ["semantic_domain", "arithmetic"], ["arithmetic_family", "addition"]],
        first_wrong_layer=None,
        first_confidence_collapse_layer=None,
        root_type="low_score_correct",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_root_viability_classifies_undervalued_correct():
    report = diagnose_root_viability(_root(), perturbation_reproduction_rate=0.8)

    assert report.classification == "undervalued_correct_root"


def test_root_viability_classifies_lucky_correct():
    root = _root(stable_prefix=[["task_scope", "programming"]], first_wrong_layer="language_target", first_confidence_collapse_layer="language_target")

    report = diagnose_root_viability(root, perturbation_reproduction_rate=0.6)

    assert report.classification == "lucky_correct_root"


def test_viability_summary_counts_low_score_correct_roots():
    reports = [
        diagnose_root_viability(_root(), perturbation_reproduction_rate=0.8),
        diagnose_root_viability(_root(stable_prefix=[["task_scope", "programming"]], first_wrong_layer="language_target"), perturbation_reproduction_rate=0.6),
    ]

    summary = summarize_viability(reports)

    assert summary["low_score_correct_count"] == 2
    assert summary["undervalued_correct_count"] == 1
    assert summary["lucky_correct_count"] == 1
