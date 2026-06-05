from jianmu.self_learning.darwinforge.linguaforge_nl_intent_schema import LinguaForgeWideNLConfig


def test_linguaforge_nl_intent_schema_contains_project_algorithm_csystems_symbol():
    assert "quicksort_ascending" in LinguaForgeWideNLConfig.algorithm_nl
    assert "split_main_algo_header" in LinguaForgeWideNLConfig.project_layout_nl
    assert "malloc_dynamic_array" in LinguaForgeWideNLConfig.csystems_nl
    assert "rename_variable" in LinguaForgeWideNLConfig.symbol_binding_nl
