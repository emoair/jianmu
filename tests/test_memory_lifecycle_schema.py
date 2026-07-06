from jianmu.self_learning.darwinforge.memory_lifecycle_schema import MemoryLifecycleRepairConfig, memory_lifecycle_contract


def test_memory_lifecycle_schema() -> None:
    cfg = MemoryLifecycleRepairConfig(dataset_samples=10)
    assert cfg.dataset_samples == 10
    contract = memory_lifecycle_contract()
    assert contract["real_promotion_enabled"] is False
    assert contract["production_support_completed"] is False
