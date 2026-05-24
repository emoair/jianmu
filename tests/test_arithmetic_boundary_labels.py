from jianmu.self_learning.darwinforge.arithmetic_boundary_labels import SUPPORTED, label_metadata


def test_non_supported_has_no_targetir_metadata():
    meta = label_metadata("hard_ood")
    assert meta["expected_action"] == "reject"
    assert meta["expected_type"] == "unsupported"


def test_supported_has_expected_output_metadata():
    meta = label_metadata(SUPPORTED)
    assert meta["expected_action"] == "accept_supported"
    assert meta["expected_type"] == "int"
