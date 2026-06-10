import json

from jianmu.self_learning.darwinforge.human_review_pack_schema import HumanReviewPackConfig
from jianmu.self_learning.darwinforge.trace_sampling_strategy import select_review_samples


def test_trace_sampling_strategy_is_deterministic(tmp_path):
    pack = _pack(tmp_path)
    config = HumanReviewPackConfig(total_review_samples=6, arithmetic_samples=1, function_samples=1, array_samples=1, function_array_samples=1, structured_recursion_samples=1, mixed_extended_ir_samples=1)
    a = select_review_samples(pack, tmp_path / "a", config)
    b = select_review_samples(pack, tmp_path / "b", config)
    assert a == b


def test_trace_sampling_strategy_covers_all_policies(tmp_path):
    pack = _pack(tmp_path)
    samples = select_review_samples(pack, tmp_path / "out", HumanReviewPackConfig())
    assert {row["policy"] for row in samples} == {
        "canonical_arithmetic_targetir",
        "canonical_function_targetir",
        "canonical_array_targetir",
        "canonical_function_array_targetir",
        "canonical_structured_recursion_targetir",
        "mixed_extended_ir_path",
    }


def _pack(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    policies = [
        "canonical_arithmetic_targetir",
        "canonical_function_targetir",
        "canonical_array_targetir",
        "canonical_function_array_targetir",
        "canonical_structured_recursion_targetir",
        "mixed_extended_ir_path",
    ]
    rows = []
    for policy in policies:
        for i in range(80):
            rows.append({"sample_id": f"v1_0_5_1_x_{i:08d}", "policy": policy, "ir_kind": policy, "builder": "b", "emitter": "ExtendedEmitterC", "source_sha256": "s", "expected_stdout": "1", "actual_stdout": "1", "passed": True, "compile_invocation_id": f"{policy}-{i}"})
    (pack / "policy_path_trace_000.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return pack

