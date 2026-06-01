from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_dataset_builder import build_mirrorforge_dataset
from jianmu.self_learning.darwinforge.mirrorforge_token_audit import audit_mirrorforge_dataset


def test_mirrorforge_token_audit(tmp_path) -> None:
    build_mirrorforge_dataset(tmp_path, minimum_samples=300, counts_by_scale={"pilot": 300})
    audit = audit_mirrorforge_dataset(tmp_path)
    assert audit["audit_passed"]
    assert audit["over_45mb_shard_count"] == 0
