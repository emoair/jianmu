from jianmu.self_learning.darwinforge.symbol_guided_renamer import guided_rename


def test_symbol_guided_renamer_preserves_scope():
    files = {"main.c": 'int compute(void){int total=1; const char *s="total"; return total;}'}
    mutated, audit = guided_rename(files, "total", "renamed_total")
    assert "renamed_total" in mutated["main.c"]
    assert '"total"' in mutated["main.c"]
    assert audit["rename_success"] is True


def test_symbol_guided_renamer_handles_shadowing():
    files = {"main.c": "int value=1; int compute(void){int value=2; return value;}"}
    mutated, audit = guided_rename(files, "value", "local_value")
    assert mutated["main.c"].count("local_value") >= 2
    assert audit["rename_success"] is True

