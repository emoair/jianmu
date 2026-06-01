from jianmu.self_learning.darwinforge.freeze_candidate_module_map import run_module_map


def test_module_map_roles_and_forbidden_influence(tmp_path):
    module_map = run_module_map(tmp_path)
    modules = {row["module"]: row for row in module_map["modules"]}
    assert modules["RedQueen"]["role"].startswith("curriculum")
    assert "production promotion" in modules["Symbiote"]["forbidden_influence"]
    assert module_map["module_map_completed"] is True
