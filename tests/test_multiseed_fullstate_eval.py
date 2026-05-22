from jianmu.self_learning.darwinforge.multiseed_fullstate_eval import run_multiseed_fullstate_eval


def test_multiseed_eval_outputs_worst_seed():
    result = run_multiseed_fullstate_eval("large", [42, 43, 44])
    assert result["seed_count"] == 3
    assert result["worst_seed"] in {42, 43, 44}


def test_multiseed_stability_requires_all_completed_seeds():
    result = run_multiseed_fullstate_eval("large", [42], {"external_ood_false_accept_rate": 0.2})
    assert result["multi_seed_stable"] is False
