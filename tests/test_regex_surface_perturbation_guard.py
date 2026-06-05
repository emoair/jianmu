from jianmu.self_learning.darwinforge.regex_surface_perturbation_guard import regex_guard


def test_regex_guard_blocks_string_literal_mutation():
    original = 'int compute(void){int total=1; const char *s="total"; return total;}'
    mutated = 'int compute(void){int renamed=1; const char *s="renamed"; return renamed;}'
    assert regex_guard(original, mutated, "total", "renamed")["string_literal_mutation_blocked"] is True


def test_regex_guard_blocks_comment_mutation():
    original = "int compute(void){int total=1; /* total */ return total;}"
    mutated = "int compute(void){int renamed=1; /* renamed */ return renamed;}"
    assert regex_guard(original, mutated, "total", "renamed")["comment_mutation_blocked"] is True


def test_regex_guard_blocks_identifier_substring_mutation():
    original = "int compute(void){int i=1; int limit=2; return i+limit;}"
    mutated = "int compute(void){int idx=1; int limidxt=2; return idx+limidxt;}"
    assert regex_guard(original, mutated, "i", "idx")["identifier_substring_mutation_blocked"] is True

