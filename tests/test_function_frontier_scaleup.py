from jianmu.self_learning.darwinforge.function_frontier_scaleup import run_function_frontier


def test_function_definition_call_frontier(tmp_path):
    result = run_function_frontier(tmp_path)
    assert result["pure_function_definition_success_rate"] >= 0.90
    assert result["function_call_success_rate"] >= 0.90
    assert result["multi_function_call_graph_success_rate"] >= 0.88
    assert result["accidental_recursion_count"] == 0
