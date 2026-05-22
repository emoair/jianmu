from jianmu.self_learning.darwinforge.ablation_harness import run_ablation_harness


def test_ablation_harness_no_root_colony():
    result = run_ablation_harness([{"raw_text": "x"}])
    variants = {row["variant"] for row in result["results"]}
    assert "no_root_colony" in variants


def test_ablation_harness_unsupported_marked_not_faked():
    result = run_ablation_harness([{"raw_text": "x"}])
    row = next(row for row in result["results"] if row["variant"] == "no_fullstate_reload")
    assert row["status"] == "unsupported"
    assert row["unsupported_reason"]
