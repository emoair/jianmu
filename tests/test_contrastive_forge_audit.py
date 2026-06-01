from __future__ import annotations

from jianmu.self_learning.darwinforge.contrastive_forge_audit import audit_contrastive_forge
from jianmu.self_learning.darwinforge.contrastive_forge_generator import generate_contrastive_forge_dataset


def test_contrastive_forge_no_current_supported_future_features(tmp_path) -> None:
    generate_contrastive_forge_dataset(tmp_path, {"pilot": 90})
    audit = audit_contrastive_forge(tmp_path)
    assert audit["audit_passed"] is True
    assert audit["function_array_recursion_current_supported_count"] == 0
