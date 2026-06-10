import json

from jianmu.self_learning.darwinforge.dry_run_coverage_review import run_dry_run_coverage_review


def test_dry_run_coverage_review_requires_all_categories(tmp_path):
    pack = tmp_path / "source" / "dry_run_trace_pack"
    pack.mkdir(parents=True)
    row = {"policy": "canonical_function_targetir", "ir_kind": "FunctionCallProgram", "compile_invocation_id": "1", "source_sha256": "s1"}
    (pack / "dry_run_policy_path_trace_000.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    result = run_dry_run_coverage_review(tmp_path / "source", tmp_path / "out", 1, 1)
    assert result["category_all_represented"] is False
