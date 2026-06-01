from __future__ import annotations

from jianmu.self_learning.darwinforge.mirrorforge_token_schema import is_raw_target_ir_dump, mirror_token_schema


def test_mirrorforge_token_schema_not_raw_target_ir() -> None:
    schema = mirror_token_schema()
    assert "PROGRAM_BEGIN" in schema["token_vocab"]
    assert not is_raw_target_ir_dump("PROGRAM_BEGIN VAR x INIT CONST 1 PROGRAM_END")
    assert is_raw_target_ir_dump('{"op":"Program"}')
