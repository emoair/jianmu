from jianmu.self_learning.darwinforge.longhaul_rolling_metrics import build_rolling_windows
from jianmu.self_learning.darwinforge.longhaul_stability_audit import audit_longhaul_stability


def test_longhaul_stability_audit():
    audit = audit_longhaul_stability(build_rolling_windows(["v0_9_23_reference"]))
    assert audit["stability_audit_completed"] is True
    assert audit["crash_count"] == 0
