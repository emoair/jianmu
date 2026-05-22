from jianmu.self_learning.darwinforge.baseline_harness import evaluate_baseline, heuristic_uses_forbidden_fields, run_baseline_harness


def test_baseline_harness_random_router():
    result = run_baseline_harness([{"raw_text": "hello"}], seeds=[42])
    assert "random_router_baseline" in result["methods_completed"]


def test_baseline_harness_heuristic_router_no_target_fields():
    sample = {"raw_text": "please calculate 3+4"}
    assert heuristic_uses_forbidden_fields([sample]) is False
    result = evaluate_baseline("heuristic_router_baseline", [sample], "quick", 42)
    assert result["forbidden_fields_used"] is False
