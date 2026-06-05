from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row
from jianmu.self_learning.darwinforge.symbol_table_builder import build_symbol_table


def test_symbol_table_builder_detects_variables_functions_params():
    row = build_symbol_binding_row(0)
    table = build_symbol_table(row["files"])
    kinds = {s["kind"] for s in table["symbols"]}
    assert {"variable", "function"}.issubset(kinds)


def test_symbol_table_builder_detects_struct_fields():
    row = build_symbol_binding_row(62)
    table = build_symbol_table(row["files"])
    assert any(s["kind"] == "struct_field" for s in table["symbols"])


def test_symbol_table_builder_detects_multifile_symbols():
    row = build_symbol_binding_row(72)
    table = build_symbol_table(row["files"])
    files = {s["file"] for s in table["symbols"]}
    assert {"main.c", "algo.c"}.issubset(files)
