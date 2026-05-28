from __future__ import annotations

from typing import Any, Dict


def supported_program_ir(value: int) -> Dict[str, Any]:
    return {"op": "Program", "body": [{"op": "Print", "value": {"op": "Int", "value": value}}]}


def canonical_program(value: int, hard: bool = False) -> str:
    kind = "nested_bounded_control" if hard else "bounded_control"
    return f"{kind}: print_int({value})"


def supported_value(index: int) -> int:
    return 1000003 + index
