from jianmu.self_learning.darwinforge.freeze_candidate_evidence_matrix import run_freeze_candidate_audit


def test_freeze_bundle_generated(tmp_path):
    result = run_freeze_candidate_audit("records", ["v0_9_20", "v0_9_20_1", "v0_9_23"], tmp_path)
    assert (tmp_path / "v1_0_freeze_candidate_bundle" / "freeze_candidate_summary.md").exists()
    assert result["readiness"]["freeze_bundle_generated"] is True


def test_readiness_release_false_without_human_review(tmp_path):
    result = run_freeze_candidate_audit("records", ["v0_9_18_2", "v0_9_20", "v0_9_20_1", "v0_9_23"], tmp_path)
    readiness = result["readiness"]
    assert readiness["ready_for_v1_0_freeze_candidate"] is True
    assert readiness["ready_for_v1_0_release"] is False
    assert "release" not in readiness["recommended_claim_level"]


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("freeze_candidate*.py"))
    assert "import expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("freeze_candidate*.py"))
    assert "openai" not in text.lower()
    assert "requests." not in text.lower()


def test_no_hardcoded_keyword_gate():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8") for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("freeze_candidate*.py"))
    assert "def keyword_rejection" not in text
    assert "keyword_gate" not in text


def test_real_promotion_disabled(tmp_path):
    result = run_freeze_candidate_audit("records", ["v0_9_23"], tmp_path)
    assert result["readiness"]["real_promotion_disabled"] is True
