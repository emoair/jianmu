from jianmu.self_learning.darwinforge.linguaforge_nl_requirement_parser import parse_nl_requirement


def test_nl_requirement_parser_extracts_algorithm_intent():
    parsed = parse_nl_requirement("帮我写升序快速排序", "algorithm_nl", "quicksort_ascending")
    assert parsed["parse_success"]
    assert parsed["intent_features"]["has_algorithm_intent"]


def test_nl_requirement_parser_extracts_csystems_intent():
    parsed = parse_nl_requirement("需要 malloc 动态数组", "csystems_nl", "malloc_dynamic_array")
    assert parsed["intent_features"]["has_csystems_intent"]


def test_nl_requirement_parser_extracts_symbol_rename_intent():
    parsed = parse_nl_requirement("把变量改名", "symbol_binding_nl", "rename_variable")
    assert parsed["intent_features"]["has_symbol_binding_intent"]
