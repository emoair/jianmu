from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.subbeam_regrowth import (
    SubBeamConfig,
    SubBeamRegrowthRequest,
    run_prefix_conditioned_subbeam,
    summarize_subbeam_results,
)


def _sample():
    return {
        "sample_id": "s-add",
        "input_text": "1+2",
        "split": "eval",
        "input_mode": "arabic_math_expression",
        "target_branch_path": [
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
            ["arithmetic_family", "addition"],
            ["structure_policy", "binary_operation"],
            ["slot_binding_policy", "surface_number_order"],
            ["target_builder", "canonical_arithmetic_targetir"],
        ],
        "target_ir_canonical": "add(lit(1),lit(2))",
        "expected_output": "3\n",
        "supported": True,
        "unsupported_reason": None,
    }


def _request(teacher_guided=False, target_option="addition"):
    return SubBeamRegrowthRequest(
        sample_id="s-add",
        raw_text="1+2",
        canonical_text="1+2",
        stable_prefix=[
            ["task_scope", "programming"],
            ["language_target", "math_expression_context"],
            ["semantic_domain", "arithmetic"],
        ],
        fork_layer="arithmetic_family",
        fork_reason="first_low_score_correct_layer",
        target_option_at_fork=target_option,
        target_option_rank=5,
        score_gap=10,
        teacher_guided=teacher_guided,
    )


def test_prefix_conditioned_subbeam_starts_from_stable_prefix():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=42)

    result = run_prefix_conditioned_subbeam(population, _sample(), _request(), SubBeamConfig(subbeam_size=4, proposals_per_layer=2, exploration_quota=0, stochastic_samples_per_layer=0, max_complete_paths=6, seed=42))

    assert result.path_count > 0
    first_path = result.generated_paths_summary[0]["decisions"]
    assert first_path[:3] == _request().stable_prefix


def test_subbeam_does_not_force_target_option_in_free_mode():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=43)

    result = run_prefix_conditioned_subbeam(population, _sample(), _request(teacher_guided=False), SubBeamConfig(subbeam_size=4, proposals_per_layer=2, exploration_quota=0, stochastic_samples_per_layer=0, max_complete_paths=6, seed=43))

    assert result.teacher_guided is False
    assert result.diagnostic_bonus_applied is False


def test_teacher_subbeam_records_diagnostic_bonus():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=44)

    result = run_prefix_conditioned_subbeam(population, _sample(), _request(teacher_guided=True), SubBeamConfig(subbeam_size=4, proposals_per_layer=2, exploration_quota=0, stochastic_samples_per_layer=0, max_complete_paths=6, seed=44))

    assert result.teacher_guided is True
    assert result.diagnostic_bonus_applied is True


def test_subbeam_rescue_rate_metric():
    result = run_prefix_conditioned_subbeam(
        LayerPreservedPopulation.initialize(population_per_layer=12, seed=45),
        _sample(),
        _request(teacher_guided=True),
        SubBeamConfig(subbeam_size=4, proposals_per_layer=2, exploration_quota=0, stochastic_samples_per_layer=0, max_complete_paths=6, seed=45),
    )
    result.rescued_from_global_failure = True

    summary = summarize_subbeam_results([result], global_failed_count=2)

    assert summary["subbeam_rescue_rate"] == 0.5


def test_report_contains_chinese_annotations():
    from examples.run_rootfork_subbeam_regrowth_probe import _report

    report = _report({"path_forcing_exact_match_rate": 1.0})

    assert "RootFork Sub-Beam Regrowth（根叉子束再生）" in report
    assert "Scale Ladder（规模阶梯）" in report


def test_free_eval_does_not_read_target_branch_path():
    from pathlib import Path

    source = Path("jianmu/self_learning/darwinforge/beam_backtracking.py").read_text(encoding="utf-8")

    assert "target_branch_path" not in source
    assert "target_ir" not in source
    assert "expected_output" not in source


def test_no_flat_classifier_imports():
    from pathlib import Path

    for path in [
        Path("jianmu/self_learning/darwinforge/rootfork.py"),
        Path("jianmu/self_learning/darwinforge/subbeam_regrowth.py"),
        Path("jianmu/self_learning/darwinforge/router_score_diagnostics.py"),
    ]:
        source = path.read_text(encoding="utf-8")
        assert "learned_router.perceptron" not in source
        assert "hashed_classifier" not in source
