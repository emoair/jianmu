from jianmu.self_learning.darwinforge.metric_provenance_audit import run_metric_provenance_audit


def test_metric_provenance_audit_detects_fixed_scaffold(tmp_path):
    result = run_metric_provenance_audit(".", tmp_path)
    assert result["metric_provenance_completed"] is True
    assert result["fixed_metric_scaffold_count"] >= 1
    assert any(row["source_type"] == "fixed_readiness_scaffold" for row in result["metrics"])

