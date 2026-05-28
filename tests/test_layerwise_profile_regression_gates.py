from jianmu.self_learning.darwinforge.layerwise_profile_regression_gates import build_layerwise_profile_regression_gates


def test_layerwise_profile_regression_gates(tmp_path):
    shadow = {"profiles": [
        {"profile_name": "current_1B_reference", "top1_correct_rate": 0.7, "candidate_miss_rate": 0.2, "stage_top1_rates": {}},
        {"profile_name": "combined_hot_rebalanced_balanced_sampling_1B", "top1_correct_rate": 0.8, "candidate_miss_rate": 0.1, "stage_top1_rates": {"if_else_basic": 0.8, "if_else_nested": 0.8, "bounded_for_loop": 0.8, "bounded_while_with_fuel": 0.8, "nested_bounded_control": 0.8, "bounded_control_hard_supported": 0.8}},
        {"profile_name": "layerwise_sparse_1B_freeze_prune", "top1_correct_rate": 0.82, "candidate_miss_rate": 0.09, "future_domain_supported_accept_rate": 0, "boundary_false_accept_rate": 0, "trap_false_accept_rate": 0, "near_ood_supported_accept_rate": 0, "stage_top1_rates": {"if_else_basic": 0.82, "if_else_nested": 0.82, "bounded_for_loop": 0.82, "bounded_while_with_fuel": 0.82, "nested_bounded_control": 0.82, "bounded_control_hard_supported": 0.82}},
    ]}
    gates = build_layerwise_profile_regression_gates(tmp_path, shadow, {"compiler_verified_correct_rate": 1.0, "permission_error_count": 0, "cleanup_failure_count": 0, "wrong_stdout_count": 0, "boundary_compiler_misroute_count": 0, "future_domain_compiled_count": 0}, {"cross_process_reload_passed": True, "child_forbidden_field_access_count": 0, "child_metrics_comparable": True}, {"layerwise_resource_overhead_acceptable": True, "layerwise_profile_cost_effective": True}, {"forbidden_field_access_count": 0, "fixed_metric_detected": False, "summary_only_detected": False, "periodic_rule_detected": False, "no_cached_compiler_result_used_as_validation": True, "real_promotion_enabled": False})
    assert gates["all_promotion_probe_gates_passed"] is True
