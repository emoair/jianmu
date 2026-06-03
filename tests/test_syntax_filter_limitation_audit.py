from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy import write_failure_taxonomy
from jianmu.self_learning.darwinforge.syntax_filter_limitation_audit import write_syntax_filter_limitation_audit


def test_syntax_filter_limitation_audit(tmp_path):
    taxonomy = write_failure_taxonomy("records/v0_9_27", tmp_path)
    result = write_syntax_filter_limitation_audit("records/v0_9_27", tmp_path, taxonomy)
    assert result["syntax_filter_used_as_correctness_evidence"] is False
    assert result["syntax_pass_but_timeout_count"] == 5
    assert result["syntax_filter_should_remain_enabled"] is True
