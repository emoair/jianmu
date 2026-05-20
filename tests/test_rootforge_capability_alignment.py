from pathlib import Path

from jianmu.self_learning.branchchain.branch_neuron import make_seed_neurons
from jianmu.self_learning.branchchain.surface_features import extract_canonical_surface_features, extract_surface_features
from jianmu.self_learning.darwinforge.capability_audit import audit_supported_sample_capability, run_path_forcing_smoke_test
from jianmu.self_learning.darwinforge.rootforge_growth_trainer import RootForgeGrowthConfig, RootForgeGrowthTrainer
from jianmu.self_learning.datasets.symbol_grounding import build_symbol_grounding_dataset
from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def _score(layer, option, features, previous=None):
    previous = previous or []
    neuron = next(n for n in make_seed_neurons(layer, _options(layer), 0) if n.option == option)
    return neuron.score(features, previous)


def _options(layer):
    from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS

    return dict(LAYER_DEFINITIONS)[layer]


def _sample(sample_id, text, target_path, target_ir, expected="0\n", structure_policy="binary_operation", expression_family="addition"):
    return {
        "sample_id": sample_id,
        "input_text": text,
        "split": "eval",
        "input_mode": "math_expression",
        "target_branch_path": target_path,
        "target_ir_canonical": target_ir,
        "expected_output": expected,
        "supported": True,
        "unsupported_reason": None,
        "structure_policy": structure_policy,
        "expression_family": expression_family,
    }


def test_branch_prior_literal_only_arithmetic_family():
    features = extract_surface_features("49")

    literal = _score("arithmetic_family", "literal_only", features)
    addition = _score("arithmetic_family", "addition", features)

    assert literal > addition


def test_branch_prior_literal_value_structure_policy():
    features = extract_surface_features("49")

    literal = _score("structure_policy", "literal_value", features)
    binary = _score("structure_policy", "binary_operation", features)

    assert literal > binary


def test_target_builder_accepts_literal_without_operator():
    features = extract_surface_features("49")

    arithmetic = _score("target_builder", "canonical_arithmetic_targetir", features)
    early_exit = _score("target_builder", "early_exit", features)

    assert arithmetic > early_exit


def test_negative_literal_not_binary_subtraction():
    features = extract_surface_features("-6")

    assert features["operator_count"] == 0
    assert features["unary_negative_only"] is True
    assert _score("arithmetic_family", "literal_only", features) > _score("arithmetic_family", "subtraction", features)


def test_surface_features_unary_negative_only():
    features = extract_canonical_surface_features("负六")

    assert features["canonical_text"] == "-6"
    assert features["unary_negative_only"] is True
    assert features["signed_literal_only"] is True


def test_surface_features_binary_minus_present():
    features = extract_surface_features("9-15")

    assert features["binary_minus_present"] is True
    assert features["operator_sequence"] == "-"


def test_path_forcing_smoke_literal_only_success():
    sample = _sample(
        "literal",
        "49",
        [
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", "literal_only"],
            ["structure_policy", "literal_value"],
            ["slot_binding_policy", "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "lit(49)",
        "49\n",
        structure_policy="literal_value",
        expression_family="literal_only",
    )

    metrics = run_path_forcing_smoke_test([sample])

    assert metrics["path_forcing_exact_match_rate"] == 1.0
    assert metrics["path_forcing_literal_only_success_rate"] == 1.0


def test_path_forcing_smoke_precedence_div_add_success():
    sample = _sample(
        "div-add",
        "24/4+3",
        [
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", "mixed_precedence"],
            ["structure_policy", "precedence_tree"],
            ["slot_binding_policy", "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "add(div(lit(24),lit(4)),lit(3))",
        "9\n",
        structure_policy="precedence_tree",
        expression_family="mixed_precedence",
    )

    metrics = run_path_forcing_smoke_test([sample])

    assert metrics["path_forcing_exact_match_rate"] == 1.0
    assert metrics["path_forcing_precedence_success_rate"] == 1.0


def test_capability_audit_distinguishes_router_vs_synthesis_failure():
    sample = _sample(
        "literal",
        "49",
        [
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", "literal_only"],
            ["structure_policy", "literal_value"],
            ["slot_binding_policy", "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "lit(49)",
        "49\n",
        structure_policy="literal_value",
        expression_family="literal_only",
    )

    audit = audit_supported_sample_capability([sample], beam_diagnostics=[{"sample_id": "literal", "correct_targetir_in_beam": False}])

    assert audit["synthesizable_by_forced_path_rate"] == 1.0
    assert audit["router_candidate_failure_rate"] == 1.0
    assert audit["synthesis_capability_failure_rate"] == 0.0


def test_capability_audit_reports_dataset_mismatch():
    sample = _sample(
        "bad-div",
        "5/2",
        [
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", "exact_division"],
            ["structure_policy", "binary_operation"],
            ["slot_binding_policy", "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "div(lit(5),lit(2))",
        "2\n",
        expression_family="exact_division",
    )

    audit = audit_supported_sample_capability([sample])

    assert audit["dataset_capability_mismatch_count"] == 1


def test_viability_metrics_are_split_separated():
    dataset = build_symbol_grounding_dataset(size=120, seed=42)
    config = RootForgeGrowthConfig.for_mode("quick", train_limit=20, eval_limit=10, ood_limit=5, generations=1, beam_size=8, population_per_layer=8)

    metrics = RootForgeGrowthTrainer(dataset["train"], dataset["eval"], dataset["ood"], config).train()

    assert "train_low_score_correct_count" in metrics
    assert "eval_low_score_correct_count" in metrics


def test_low_score_correct_without_action_is_zero():
    dataset = build_symbol_grounding_dataset(size=120, seed=42)
    config = RootForgeGrowthConfig.for_mode("quick", train_limit=20, eval_limit=10, ood_limit=5, generations=1, beam_size=8, population_per_layer=8)

    metrics = RootForgeGrowthTrainer(dataset["train"], dataset["eval"], dataset["ood"], config).train()

    assert metrics["low_score_correct_without_action_count"] == 0


def test_artifact_suffix_strip_preserves_raw_text():
    result = canonicalize_symbols("24/4+3（sample-001）")

    assert result.raw_text == "24/4+3（sample-001）"
    assert "stripped_dataset_artifact_suffix" in result.warnings


def test_artifact_suffix_strip_canonical_text_clean():
    result = canonicalize_symbols("24/4+3(sample-001)")

    assert result.canonical_text == "24/4+3"


def test_report_contains_chinese_annotations(tmp_path):
    from examples.run_rootforge_capability_alignment_probe import _report

    report = _report({"path_forcing_exact_match_rate": 1.0})

    assert "RootForge Capability Alignment（根铸能力对齐）" in report
    assert "Path-Forcing Smoke Test（强制路径冒烟测试）" in report


def test_no_expression_oracle_import():
    source = Path("jianmu/self_learning/darwinforge/capability_audit.py").read_text(encoding="utf-8")

    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source


def test_no_external_api_calls():
    source = Path("jianmu/self_learning/darwinforge/capability_audit.py").read_text(encoding="utf-8")

    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source


def test_candidate_generation_does_not_use_targetir_or_target_branch_path():
    source = Path("jianmu/self_learning/darwinforge/beam_backtracking.py").read_text(encoding="utf-8")

    assert "target_ir" not in source
    assert "expected_output" not in source
    assert "target_branch_path" not in source
