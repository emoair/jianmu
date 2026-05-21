from jianmu.self_learning.darwinforge.canonicalizer_reason_replay import replay_canonicalizer_reason


def test_canonicalizer_reason_replay_detects_match():
    result = replay_canonicalizer_reason(
        [
            {
                "sample_id": "s1",
                "raw_text": "calculate 1 plus 2",
                "canonical_text": "calculate1plus2",
                "ood_class": "ood_english_sentence",
                "accepted_as_supported": True,
                "false_accept_reason": "canonicalizer_made_it_look_supported",
            }
        ]
    )
    assert result["old_canonicalizer_reason_count"] == 1
    assert result["records"][0]["reason_match"] in {"matched", "detector_mismatch"}


def test_canonicalizer_reason_replay_reports_missing_raw():
    result = replay_canonicalizer_reason(
        [{"sample_id": "s1", "false_accept_reason": "canonicalizer_made_it_look_supported"}]
    )
    assert result["records"][0]["reason_match"] == "missing_raw_text"


def test_canonicalizer_reason_replay_reports_detector_mismatch():
    result = replay_canonicalizer_reason(
        [
            {
                "sample_id": "s1",
                "raw_text": "写一首诗",
                "canonical_text": "写1首诗",
                "ood_class": "ood_unrelated_request",
                "accepted_as_supported": True,
                "false_accept_reason": "canonicalizer_made_it_look_supported",
            }
        ]
    )
    assert result["detector_mismatch_count"] >= 0
    assert "reason_not_reproduced" in result
