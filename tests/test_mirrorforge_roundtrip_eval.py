from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset
from jianmu.self_learning.darwinforge.mirrorforge_roundtrip_eval import run_mirrorforge_roundtrip_eval


def test_mirrorforge_roundtrip_eval(tmp_path) -> None:
    build_mirrorforge_dataset(tmp_path, minimum_samples=300, counts_by_scale={"pilot": 300})
    result = run_mirrorforge_roundtrip_eval(tmp_path)
    assert result["token_to_ir_success_rate"] >= 0.99
    assert result["wrong_stdout_count"] == 0
