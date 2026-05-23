import json

from jianmu.self_learning.darwinforge.real_longrun_checkpoint import RealLongrunCheckpointWriter


def test_real_longrun_checkpoint_writes_jsonl(tmp_path):
    path = tmp_path / "checkpoints.jsonl"
    RealLongrunCheckpointWriter(path).write({"mode": "real-mini", "status": "completed"})
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["mode"] == "real-mini"
