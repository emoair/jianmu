from jianmu.self_learning.darwinforge.turing_frontier_tokens import TURING_FRONTIER_TOKENS


def test_turing_frontier_tokens_include_frontier_ops():
    for token in ["WHILE_UNBOUNDED", "RECURSIVE_FUNCTION", "COUNTER_DECJZ", "PROGRAM_COUNTER", "STATE_GROW"]:
        assert token in TURING_FRONTIER_TOKENS
