from jianmu.self_learning.darwinforge.counter_machine_mapping import counter_machine_witnesses, run_constructive_mapping


def test_counter_machine_mapping_witnesses(tmp_path):
    witnesses = counter_machine_witnesses()
    assert len(witnesses) == 10
    result = run_constructive_mapping(tmp_path)
    assert result["counter_machine_mapping_positive"] is True
    assert result["formal_proof_completed"] is False
