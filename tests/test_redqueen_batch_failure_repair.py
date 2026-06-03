from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy import write_failure_taxonomy
from jianmu.self_learning.darwinforge.redqueen_batch_failure_repair import write_redqueen_repair_assignments


def test_redqueen_repair_assignments_no_blacklist(tmp_path):
    taxonomy = write_failure_taxonomy("records/v0_9_27", tmp_path)
    result = write_redqueen_repair_assignments(tmp_path, taxonomy)
    assert result["assignments_completed"] is True
    assert all(a["no_blacklist_policy"] for a in result["assignments"])
    assert all(a["no_runtime_gate_policy"] for a in result["assignments"])
