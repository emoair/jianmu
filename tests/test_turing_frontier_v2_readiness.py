from jianmu.self_learning.darwinforge.turing_frontier_v2_readiness import build_turing_frontier_v2_readiness


def test_dataset_v2_compiler_spot_blocks_future_compile(tmp_path):
    result = build_turing_frontier_v2_readiness(tmp_path, {"scales": {"pilot": {"audit_passed": True, "total_count": 1}}}, {"dataset_v2_ready_for_active_generation_loop": True, "dataset_v2_ready_for_function_array_frontier_probe": True}, {"backend_claim_safe": True, "future_domain_compiled_count": 0})
    assert result["dataset_v2_compiler_spot_clean"] is True
