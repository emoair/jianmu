from jianmu.self_learning.darwinforge.windows_memory_attribution_schema import WindowsMemoryAttributionConfig, windows_memory_attribution_contract


def test_windows_memory_attribution_schema() -> None:
    cfg = WindowsMemoryAttributionConfig(duration_minutes=1)
    assert cfg.duration_minutes == 1
    contract = windows_memory_attribution_contract()
    assert contract["real_promotion_enabled"] is False
    assert contract["production_support_completed"] is False
