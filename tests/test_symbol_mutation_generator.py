from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row


def test_symbol_mutation_generator_variable_rename():
    row = build_symbol_binding_row(0)
    assert row["binding_validation"]["rename_success"] is True


def test_symbol_mutation_generator_function_rename():
    row = build_symbol_binding_row(1)
    assert row["source_hash_before"] != row["source_hash_after"]


def test_symbol_mutation_generator_struct_field_rename():
    row = build_symbol_binding_row(62)
    assert row["binding_family"] == "struct_binding"
    assert row["binding_validation"]["rename_success"] is True


def test_symbol_mutation_generator_multifile_consistency():
    row = build_symbol_binding_row(72)
    assert row["project_layout"] == "multi_file"
    assert row["binding_validation"]["header_source_consistent"] is True
