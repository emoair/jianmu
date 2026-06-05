from jianmu.self_learning.darwinforge.symbol_binding_schema import SymbolBindingFeatureConfig, build_symbol_binding_row


def test_symbol_binding_config_contains_all_families():
    families = SymbolBindingFeatureConfig.families()
    for name in ["identifier_binding", "scope_binding", "pointer_binding", "malloc_binding", "fileio_binding", "struct_binding", "multifile_binding", "string_comment_guard"]:
        assert name in families
        assert families[name]


def test_symbol_binding_schema_row_fields():
    row = build_symbol_binding_row(0)
    assert row["dataset_version"] == "v1.0.4.1_symbol_binding_longhaul"
    assert row["rename_policy"]["ast_symbol_table_guided"] is True
    assert row["provenance"]["external_api_used"] is False

