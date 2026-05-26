from __future__ import annotations

from jianmu.self_learning.darwinforge.turing_substrate_boundary_labels import SUPPORTED, label_metadata


def test_turing_substrate_rejects_recursion_as_supported() -> None:
    assert label_metadata("future_domain_candidate")["expected_action"] == "isolate_future"
    assert label_metadata("unsupported_program_boundary")["expected_action"] == "reject"


def test_turing_substrate_rejects_pointers_arrays_functions_as_supported() -> None:
    assert label_metadata("near_ood_program")["expected_action"] == "quarantine"
    assert label_metadata(SUPPORTED)["expected_action"] == "accept_supported"
