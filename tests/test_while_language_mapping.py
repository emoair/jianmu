from jianmu.self_learning.darwinforge.while_language_mapping import while_language_witnesses, run_constructive_mapping


def test_while_language_mapping_witnesses(tmp_path):
    witnesses = while_language_witnesses()
    assert len(witnesses) == 10
    result = run_constructive_mapping(tmp_path)
    assert result["while_language_mapping_positive"] is True
    assert result["formal_proof_completed"] is False
