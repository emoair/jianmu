import json

from jianmu.self_learning.darwinforge.failure_taxonomy_completeness_audit import REQUIRED_FAILURES, audit_failure_taxonomy_completeness


def test_failure_taxonomy_completeness_requires_blocking_failures(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rows = [{"failure_type": item, "severity": "blocking", "production_claim_allowed": False} for item in REQUIRED_FAILURES]
    rows = [row for row in rows if row["failure_type"] != "timeout"]
    (source / "failure_taxonomy.json").write_text(json.dumps({"failures": rows}), encoding="utf-8")
    result = audit_failure_taxonomy_completeness(source, tmp_path / "out")
    assert result["failure_taxonomy_audit_passed"] is False
    assert "timeout" in result["missing_failure_types"]
