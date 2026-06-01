from jianmu.self_learning.darwinforge.symbiote_turing_frontier_probe import symbiote_frontier_probe


def test_symbiote_turing_frontier_probe(tmp_path):
    result = symbiote_frontier_probe(tmp_path)
    assert result["best_experiment_group"] == "redqueen_hydrabudget_turing_frontier_symbiote"
    assert result["comfort_zone_audit_passed"] is True
