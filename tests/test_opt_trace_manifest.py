from jianmu.self_learning.darwinforge.opt_trace_manifest import build_opt_trace_manifest


def test_opt_trace_manifest(tmp_path) -> None:
    path = build_opt_trace_manifest(tmp_path, [{"phase": "x"}])
    assert path.exists()
    assert "phase" in path.read_text(encoding="utf-8")

