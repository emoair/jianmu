from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_nl_bridge_diagnostic import build_nl_bridge_diagnostic


def test_mirrorforge_nl_bridge_diagnostic_no_nl_claim(tmp_path):
    result = build_nl_bridge_diagnostic(tmp_path)
    assert result["ready_for_nl_to_mirrortoken_adapter_probe"] is True
    assert result["natural_language_layer_completed"] is False
