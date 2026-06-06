from pathlib import Path

from jianmu.self_learning.darwinforge.evidence_trace_pack_builder import build_evidence_trace_pack


def test_evidence_trace_pack_builder(tmp_path):
    records = tmp_path / "records"
    current = records / "v0_9_28_1"
    current.mkdir(parents=True)
    (current / "full_compile_50k_trace_000.jsonl").write_text('{"sample":"a"}\n', encoding="utf-8")
    result = build_evidence_trace_pack(records, records / "out", package_records=records / "package_missing", current_trace_records=current)
    assert result["evidence_trace_pack_generated"] is True
    assert result["raw_trace_available_in_v1_package"] is False
    assert result["raw_trace_available_in_current_workspace"] is True
    assert Path(records / "out" / "evidence_trace_pack" / "trace_manifest.json").exists()

