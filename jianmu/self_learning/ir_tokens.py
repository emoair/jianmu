from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jianmu.emitter_c import CEmitter
from jianmu.ir import ProgramIR, SumExpression, Variable


@dataclass(frozen=True)
class IRToken:
    type: str
    value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


SUPPORTED_TOKEN_TYPES = {
    "INCLUDE_STDIO",
    "MAIN_BEGIN",
    "LITERAL_INT",
    "ADD",
    "PRINT_EXPR",
    "MAIN_END",
}


def expected_binary_add_tokens(left: int, right: int) -> List[IRToken]:
    return [
        IRToken("INCLUDE_STDIO"),
        IRToken("MAIN_BEGIN"),
        IRToken("LITERAL_INT", left),
        IRToken("LITERAL_INT", right),
        IRToken("ADD"),
        IRToken("PRINT_EXPR"),
        IRToken("MAIN_END"),
    ]


def tokens_to_program_ir(tokens: List[IRToken]) -> ProgramIR:
    literal_values = _validate_binary_add_tokens(tokens)
    variables = [
        Variable("a", value=literal_values[0]),
        Variable("b", value=literal_values[1]),
    ]
    return ProgramIR(
        includes=["stdio.h"],
        variables=variables,
        expression=SumExpression(["a", "b"]),
        print=True,
        return_code=0,
    )


def tokens_to_c_code(tokens: List[IRToken]) -> str:
    return CEmitter().emit(tokens_to_program_ir(tokens))


def _validate_binary_add_tokens(tokens: List[IRToken]) -> List[int]:
    expected_types = [
        "INCLUDE_STDIO",
        "MAIN_BEGIN",
        "LITERAL_INT",
        "LITERAL_INT",
        "ADD",
        "PRINT_EXPR",
        "MAIN_END",
    ]
    actual_types = [token.type for token in tokens]
    if actual_types != expected_types:
        raise ValueError(f"unsupported IR token sequence: {actual_types}")

    values = [tokens[2].value, tokens[3].value]
    if not all(isinstance(value, int) for value in values):
        raise ValueError("LITERAL_INT tokens require integer values")
    return values

