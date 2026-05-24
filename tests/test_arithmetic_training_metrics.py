from jianmu.self_learning.darwinforge.arithmetic_training_metrics import stage_metric_row


def test_arithmetic_training_metrics_stage_row():
    row = stage_metric_row(
        "mixed_final",
        10,
        5,
        {"supported_candidate_in_beam_rate": 0.8, "supported_correct_output_in_beam_rate": 0.8, "false_accept_rate": 0.1, "false_reject_rate": 0.2},
        {"supported_candidate_in_beam_rate": 1.0, "supported_correct_output_in_beam_rate": 1.0, "false_accept_rate": 0.0, "false_reject_rate": 0.0, "forbidden_field_access_count": 0},
        10,
        2,
        0.01,
    )
    assert row["candidate_hit_after"] == 1.0
    assert row["stage_passed"] is True
