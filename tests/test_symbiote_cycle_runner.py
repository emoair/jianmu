from jianmu.self_learning.darwinforge.symbiote_cycle_runner import run_symbiote_cycles


def test_symbiote_training_metrics(tmp_path):
    result = run_symbiote_cycles(tmp_path)
    best = max(result["runs"], key=lambda row: row["top1"])
    assert best["experiment_group"] == "redqueen_hydrabudget_symbiote"
    assert best["top1"] > 0.9224
