import json

from jianmu.self_learning.darwinforge.compiler_invocation_integrity_audit import audit_v1_0_8_8_compiler_claim


def test_compiler_claim_audit_rejects_summary_only_counter(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "endurance_summary.json").write_text(json.dumps({"real_compiler_invocations": 10}), encoding="utf-8")
    result = audit_v1_0_8_8_compiler_claim(source, tmp_path / "out")
    assert result["v1_0_8_8_compiler_claim_downgraded"] is True
    assert result["compiler_claim_integrity_status"] == "unverified_summary_only"

