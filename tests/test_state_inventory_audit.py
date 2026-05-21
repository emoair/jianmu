from jianmu.self_learning.darwinforge.state_inventory_audit import run_state_inventory_audit


def test_state_inventory_distinguishes_summary_from_runtime_state(tmp_path):
    records = tmp_path / "records"
    records.mkdir()
    (records / "persisted_router_metrics.json").write_text("{}", encoding="utf-8")
    report = run_state_inventory_audit(records)
    assert report["branchchain_state_found"] is True
    assert report["evaluation_summary_only_found"] is True
    assert "trained_branch_population" in report["missing_for_full_state"]
