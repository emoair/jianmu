from jianmu.self_learning.darwinforge.turing_frontier_v2_grammar import is_current_supported, support_status_for_category


def test_turing_frontier_v2_audit_blocks_future_targets():
    assert is_current_supported("near_supported_pure_function") is False
    assert support_status_for_category("future_bounded_recursion_candidate") == "future_domain"
