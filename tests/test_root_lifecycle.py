from jianmu.self_learning.darwinforge.root_lifecycle import RootLifecycleConfig, update_root_lifecycle


def test_root_lifecycle_starvation_counter():
    states = {}

    metrics = update_root_lifecycle(states, [{"root_id": "r1", "sample_id": "s", "path_signature": "p"}], {}, RootLifecycleConfig(), generation=1)

    assert states["r1"].starvation_counter == 1
    assert metrics["starving_root_count"] == 1


def test_root_lifecycle_necrosis_archive():
    states = {}
    cfg = RootLifecycleConfig(necrosis_threshold=1)

    metrics = update_root_lifecycle(states, [{"root_id": "r1", "sample_id": "s", "path_signature": "p"}], {}, cfg, generation=1)

    assert states["r1"].state == "necrotic_archived"
    assert metrics["necrotic_archived_count"] == 1


def test_root_lifecycle_replacement_request_from_stable_prefix():
    states = {}
    candidate = {"root_id": "r1", "sample_id": "s", "path_signature": "p", "stable_prefix": [["task_scope", "programming"]]}

    metrics = update_root_lifecycle(states, [candidate], {}, RootLifecycleConfig(), generation=1)

    assert metrics["replacement_root_count"] == 1


def test_necrotic_root_does_not_consume_active_budget():
    states = {}
    cfg = RootLifecycleConfig(necrosis_threshold=1, max_active_roots=0)

    metrics = update_root_lifecycle(states, [{"root_id": "r1", "sample_id": "s", "path_signature": "p"}], {}, cfg, generation=1)

    assert metrics["active_root_count"] == 0
    assert metrics["necrotic_archived_count"] >= 1
