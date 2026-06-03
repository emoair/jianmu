from jianmu.self_learning.darwinforge.array_frontier_scaleup import run_array_frontier


def test_array_declaration_read_write_loop(tmp_path):
    result = run_array_frontier(tmp_path)
    assert result["fixed_array_declaration_success_rate"] >= 0.90
    assert result["array_read_success_rate"] >= 0.90
    assert result["array_write_success_rate"] >= 0.88
    assert result["array_loop_success_rate"] >= 0.88
    assert result["pointer_like_array_misroute_count"] == 0
