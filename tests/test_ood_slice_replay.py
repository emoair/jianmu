import json
import subprocess

from jianmu.self_learning.darwinforge.ood_slice_replay import load_v081_ood_slice


def test_ood_slice_replay_loads_source_metadata(tmp_path, monkeypatch):
    row = {
        "sample_id": "s1",
        "raw_text": "calculate 1 plus 2",
        "canonical_text": "calculate1plus2",
        "ood_class": "ood_english_sentence",
        "accepted_as_supported": True,
        "false_accept_reason": "canonicalizer_made_it_look_supported",
        "run_id": "r1",
    }

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(row) + "\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    loaded = load_v081_ood_slice(tmp_path, "source-branch")
    assert loaded["source_branch"] == "source-branch"
    assert loaded["replay_sample_count"] == 1
    assert loaded["records"][0]["original_record_path"].endswith("ood_guard_stress.jsonl")


def test_ood_slice_replay_marks_partial_when_raw_missing(tmp_path, monkeypatch):
    row = {"sample_id": "s1", "canonical_text": "1+2"}

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps(row) + "\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    loaded = load_v081_ood_slice(tmp_path, "source-branch")
    assert loaded["partial_replay"] is True
    assert loaded["missing_field_counts"]["raw_text"] == 1
