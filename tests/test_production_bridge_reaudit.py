from jianmu.self_learning.darwinforge.production_bridge_reaudit import run_production_bridge_reaudit


def test_production_bridge_reaudit_detects_extended_ir_paths(tmp_path):
    result = run_production_bridge_reaudit(tmp_path)
    assert result["reaudit_completed"] is True
    assert result["function_ir_path_confirmed"] is True
    assert result["array_ir_path_confirmed"] is True
    assert result["function_array_ir_path_confirmed"] is True
    assert result["recursion_ir_path_confirmed"] is True
    assert result["phase_a_passed"] is True

