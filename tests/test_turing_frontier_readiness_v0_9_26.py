from jianmu.self_learning.darwinforge.turing_frontier_schema import run_turing_frontier_probe


def test_formal_turing_completeness_not_claimed(tmp_path):
    result = run_turing_frontier_probe(tmp_path / "records", tmp_path / "dataset", target_samples=1000, compiler_target=4, compile_worker_count=2)
    readiness = result["readiness"]
    assert readiness["formal_turing_completeness_proven"] is False
    assert readiness["ready_for_v1_0_release"] is False


def test_ready_for_release_false(tmp_path):
    result = run_turing_frontier_probe(tmp_path / "records", tmp_path / "dataset", target_samples=1000, compiler_target=4, compile_worker_count=2)
    assert result["readiness"]["ready_for_v1_0_release"] is False
    assert result["readiness"]["recommended_claim_level"] == "endurance_partial_needs_rerun"


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*frontier*.py"))
    assert "import expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*frontier*.py"))
    assert "openai" not in text.lower()
    assert "requests." not in text.lower()


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("*frontier*.py"))
    assert "keyword_gate" not in text
    assert "keyword rejection gate" not in text


def test_real_promotion_disabled(tmp_path):
    result = run_turing_frontier_probe(tmp_path / "records", tmp_path / "dataset", target_samples=1000, compiler_target=4, compile_worker_count=2)
    assert result["readiness"]["ready_for_v1_0_release"] is False
