from jianmu.self_learning.darwinforge.redqueen_symbol_binding_curriculum import redqueen_curriculum


def test_redqueen_symbol_binding_curriculum_assignments():
    curriculum = redqueen_curriculum()
    for name in ["variable_binding_assignment", "regex_guard_assignment", "compiler_accounting_guard_assignment"]:
        assert name in curriculum
        assert curriculum[name]["safety_contract"] == "symbol binding contract"

