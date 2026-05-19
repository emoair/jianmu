from jianmu.self_learning.preprocessing.symbol_canonicalizer import canonicalize_symbols


def test_canonicalize_single_digits():
    assert canonicalize_symbols("三加四").canonical_text == "3+4"


def test_canonicalize_two_digit_chinese_numbers():
    assert canonicalize_symbols("十一减五").canonical_text == "11-5"
    assert canonicalize_symbols("二十加三十").canonical_text == "20+30"


def test_canonicalize_negative_chinese_numbers():
    assert canonicalize_symbols("负三乘四").canonical_text == "-3*4"
    assert canonicalize_symbols("负十四加二").canonical_text == "-14+2"


def test_canonicalize_add_sub_mul_div_words():
    assert canonicalize_symbols("三加四").canonical_text == "3+4"
    assert canonicalize_symbols("三减四").canonical_text == "3-4"
    assert canonicalize_symbols("三乘四").canonical_text == "3*4"
    assert canonicalize_symbols("十二除以三").canonical_text == "12/3"


def test_canonicalize_mixed_zh_arabic():
    assert canonicalize_symbols("三加4").canonical_text == "3+4"
    assert canonicalize_symbols("3加四").canonical_text == "3+4"


def test_canonicalize_parenthesis_phrase():
    assert canonicalize_symbols("括号里三加四再乘五").canonical_text == "(3+4)*5"
    assert canonicalize_symbols("（三加四）乘五").canonical_text == "(3+4)*5"


def test_source_map_contains_raw_and_canonical():
    result = canonicalize_symbols("三加二")
    assert {"raw": "三", "canonical": "3", "type": "NUM", "span": [0, 1], "confidence": 1.0} in result.source_map
    assert any(item["raw"] == "加" and item["canonical"] == "+" for item in result.source_map)


def test_canonicalizer_does_not_emit_targetir():
    result = canonicalize_symbols("三加二").to_dict()
    assert "target_ir" not in result
    assert "target_ir_canonical" not in result
    assert "add(lit" not in str(result)


def test_canonicalizer_does_not_emit_c_source():
    result = canonicalize_symbols("三加二").to_dict()
    assert "c_program" not in result
    assert "#include" not in str(result)
    assert "printf" not in str(result)


def test_fail_open_on_unknown_text():
    result = canonicalize_symbols("写一首诗")
    assert result.canonical_text
    assert result.raw_text == "写一首诗"


def test_no_expression_oracle_import_in_canonicalizer():
    import inspect
    import jianmu.self_learning.preprocessing.symbol_canonicalizer as module

    assert "expression_oracle" not in inspect.getsource(module)


def test_no_external_api_calls():
    import inspect
    import jianmu.self_learning.preprocessing.symbol_canonicalizer as module

    source = inspect.getsource(module)
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source.lower()


def test_extract_canonical_surface_features_keeps_boundary():
    from jianmu.self_learning.branchchain.surface_features import extract_canonical_surface_features

    features = extract_canonical_surface_features("三加四")
    assert features["canonical_text"] == "3+4"
    assert features["signed_numbers"] == [3, 4]
    assert features["operator_sequence"] == "+"
    assert "target_ir_canonical" not in features
    assert "expected_output" not in features
