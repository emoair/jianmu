from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, parse_metrics


def test_csystems_project_parser():
    rows = [build_csystems_row(i) for i in range(100)]
    assert parse_metrics(rows)["csystems_parse_success_rate"] >= 0.88
