from jianmu.self_learning.darwinforge.arithmetic_probe_comparison_pack import write_arithmetic_comparison_pack


def test_arithmetic_probe_comparison_pack_outputs(tmp_path):
    result = write_arithmetic_comparison_pack(
        tmp_path,
        [{"stage_name": "mixed_final", "candidate_hit_after": 1.0}],
        {"by_stage": {"precedence": {"sample_count": 1}}},
        {"by_category": [{"category": "hard_ood", "false_accept_rate": 0.0}]},
        {"compiler_backend_type": "internal_evaluator"},
        {"actual_train_iterated_count": 1},
        {"cross_process_reload_passed": True},
        {"recommended_claim_level": "arithmetic_probe_positive_signal", "ready_for_arithmetic_probe_claim": True},
    )
    assert any(path.endswith("arithmetic_stage_metrics.csv") for path in result["comparison_data_paths"])
    assert (tmp_path / "arithmetic_probe_summary.md").exists()
