import json

from jianmu.self_learning.darwinforge.controlled_opt_in_approval_schema import ApprovalGateConfig
from jianmu.self_learning.darwinforge.evidence_sampling_review import run_evidence_sampling_review


def test_evidence_sampling_review_requires_hash_validity(tmp_path):
    source = tmp_path / "source"
    pack = source / "controlled_support_trace_pack"
    pack.mkdir(parents=True)
    positive = {"sample_id": "p", "category": "function", "passed": True}
    negative = {"sample_id": "n", "category": "unsupported_function_shape_rejection", "passed": True, "compile_invoked": False}
    rollback = {"sample_id": "r", "category": "opt_in_rollback", "passed": True}
    policy = {"sample_id": "pp", "builder": "b", "ir_kind": "i", "emitter": "e"}
    stdout = {"sample_id": "s", "passed": True}
    for name, row in [
        ("support_candidate_positive_trace_000.jsonl", positive),
        ("support_candidate_negative_trace_000.jsonl", negative),
        ("support_candidate_rollback_trace_000.jsonl", rollback),
        ("support_candidate_policy_path_trace_000.jsonl", policy),
        ("support_candidate_stdout_comparison_000.jsonl", stdout),
    ]:
        (pack / name).write_text(json.dumps(row) + "\n", encoding="utf-8")
    result = run_evidence_sampling_review(source, tmp_path / "out", ApprovalGateConfig(positive_samples=1, negative_samples=1, rollback_samples=1, policy_path_samples=1, stdout_samples=1, unsupported_rejection_samples=1, default_blocking_samples=0))
    assert result["sample_hashes_valid"] is True
    assert result["evidence_sampling_passed"] is True
