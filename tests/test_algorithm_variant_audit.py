from jianmu.self_learning.darwinforge.algorithm_variant_audit import audit_variant_rows
from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row


def test_variant_audit_contract_clean():
    rows = [build_variant_row("pilot", i) for i in range(100)]
    audit = audit_variant_rows(rows)
    assert audit["token_contains_c_source_count"] == 0
    assert audit["unsupported_has_targetir_count"] == 0
    assert audit["audit_passed"] is True
