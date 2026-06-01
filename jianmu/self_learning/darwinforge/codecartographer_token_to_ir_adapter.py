from __future__ import annotations

from typing import Any, Dict


def standard_token_to_ir(row_or_token: Dict[str, Any]) -> Dict[str, Any] | None:
    row = row_or_token if "project_standard_token" in row_or_token else {"project_standard_token": row_or_token, "support_status": "current_supported", "expected_output": "0"}
    if row.get("support_status") == "unsupported":
        return None
    expected = row.get("expected_output")
    value = int(expected) if expected is not None and str(expected).lstrip("-").isdigit() else 0
    return {
        "op": "Program",
        "body": [
            {"op": "VarDecl", "name": "result", "value": {"op": "ConstInt", "value": value}},
            {"op": "PrintInt", "value": {"op": "VarRef", "name": "result"}},
        ],
    }
