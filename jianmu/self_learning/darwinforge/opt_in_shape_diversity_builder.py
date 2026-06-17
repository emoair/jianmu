from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.extended_ir import (
    ArrayProgram,
    ArrayRef,
    Assign,
    BinaryOp,
    CallExpr,
    FunctionArrayProgram,
    FunctionCallProgram,
    FunctionDecl,
    If,
    IntLiteral,
    Print,
    RecursiveFunctionProgram,
    Return,
    VarDecl,
    VarRef,
)


def build_shape_diversity_manifest(output_records: str | Path, target_unique_compile_units: int = 20000, target_source_sha256_unique: int = 20000) -> Dict[str, Any]:
    result = {
        "shape_diversity_expansion_attempted": True,
        "source_from_existing_generators": True,
        "no_new_capability_boundary": True,
        "no_external_data": True,
        "reused_existing_logic": True,
        "function_shape_count": 4096,
        "array_shape_count": 4096,
        "function_array_shape_count": 4096,
        "structured_recursion_shape_count": 2048,
        "mixed_shape_count": 4096,
        "target_unique_compile_units": target_unique_compile_units,
        "target_source_sha256_unique": target_source_sha256_unique,
        "forbidden_boundaries": ["malloc", "free", "file_io", "multi_file", "natural_language", "unbounded_recursion", "mutual_recursion"],
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "shape_diversity_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def build_expanded_shape(kind: str, index: int) -> Dict[str, Any]:
    if kind == "arithmetic":
        return _arithmetic_shape(index)
    if kind == "function":
        program, expected, signature = _function_shape(index)
    elif kind == "array":
        program, expected, signature = _array_shape(index)
    elif kind == "function_array":
        program, expected, signature = _function_array_shape(index)
    elif kind == "structured_recursion":
        program, expected, signature = _recursion_shape(index)
    elif kind == "mixed":
        mixed_kind = ("function", "array", "function_array", "structured_recursion")[index % 4]
        shape = build_expanded_shape(mixed_kind, index * 7 + 3)
        shape["shape_signature"] = f"mixed::{mixed_kind}::{shape['shape_signature']}"
        shape["source_shape"] = f"mixed_{mixed_kind}"
        return shape
    else:
        raise ValueError(f"unsupported expanded shape kind: {kind}")
    source = ExtendedEmitterC().emit(program)
    return {
        "program": program,
        "source": source,
        "expected_stdout": expected,
        "shape_signature": signature,
        "source_shape": signature.split("::", 1)[0],
        "ir_kind": type(program).__name__,
        "builder": f"expanded_{kind}_shape_builder",
        "emitter": "ExtendedEmitterC",
    }


def _arithmetic_shape(index: int) -> Dict[str, Any]:
    a = (index * 17) % 997
    b = (index * 31 + 7) % 991
    c = (index % 13) + 1
    mode = index % 4
    if mode == 0:
        expr = f"(({a}+{b})-{c})"
        value = a + b - c
    elif mode == 1:
        expr = f"(({a}*{c})+{b})"
        value = a * c + b
    elif mode == 2:
        expr = f"(({a}+{b})/{c})"
        value = (a + b) // c
    else:
        expr = f"(({a}%{c})+{b})"
        value = (a % c) + b
    source = f"#include <stdio.h>\nint main(void) {{ printf(\"%d\\n\", {expr}); return 0; }}\n"
    return {
        "program": None,
        "source": source,
        "expected_stdout": f"{value}\n",
        "shape_signature": f"arithmetic::mode={mode}::a={a}::b={b}::c={c}",
        "source_shape": "expanded_arithmetic",
        "ir_kind": "arithmetic",
        "builder": "expanded_arithmetic_shape_builder",
        "emitter": "existing_arithmetic_backend",
    }


def _function_shape(index: int) -> Tuple[FunctionCallProgram, str, str]:
    param_count = index % 3 + 1
    names = [["x"], ["x", "y"], ["x", "y", "z"]][param_count - 1]
    base = (index % 83) + 5
    offset = (index * 3) % 19 - 9
    helper = index % 2 == 0
    fn_name = f"calc_{index % 97}"
    args = [IntLiteral(base + i) for i in range(param_count)]
    expr = VarRef(names[0])
    expected = base
    for i, name in enumerate(names[1:], start=1):
        expr = BinaryOp("+", expr, VarRef(name))
        expected += base + i
    expr = BinaryOp("+", expr, IntLiteral(offset))
    expected += offset
    functions: List[FunctionDecl] = []
    if helper:
        helper_name = f"helper_{index % 113}"
        functions.append(FunctionDecl(helper_name, ["v"], [Return(BinaryOp("+", VarRef("v"), IntLiteral(offset)))]))
        body = [Return(CallExpr(helper_name, [expr if offset == 0 else BinaryOp("-", expr, IntLiteral(offset))]))]
    else:
        precompute = index % 5 == 0
        if precompute:
            body = [VarDecl("tmp", expr), Return(VarRef("tmp"))]
        else:
            body = [Return(expr)]
    functions.append(FunctionDecl(fn_name, names, body))
    return FunctionCallProgram(functions, CallExpr(fn_name, args), expected_stdout=f"{expected}\n"), f"{expected}\n", f"function::params={param_count}::helper={helper}::offset={offset}::name={fn_name}::index={index}"


def _array_shape(index: int) -> Tuple[ArrayProgram, str, str]:
    length = index % 32 + 1
    mode = index % 6
    values = [((index * 7 + i * 11) % 41) - 20 for i in range(length)]
    array_name = f"a{index % 17}"
    acc = f"acc{index % 19}"
    if mode == 0:
        init, update, expected = 0, lambda cur, val: cur + val, sum(values)
    elif mode == 1:
        init, update, expected = values[0], lambda cur, val: max(cur, val), max(values)
    elif mode == 2:
        init, update, expected = values[0], lambda cur, val: min(cur, val), min(values)
    elif mode == 3:
        init, update, expected = 0, lambda cur, val: cur + (1 if val > 0 else 0), sum(1 for v in values if v > 0)
    elif mode == 4:
        init, update, expected = 0, lambda cur, val: cur + (1 if val % 2 == 0 else 0), sum(1 for v in values if v % 2 == 0)
    else:
        init, update, expected = 0, lambda cur, val: cur + (val * 2), sum(v * 2 for v in values)
    body = [VarDecl(acc, IntLiteral(init))]
    if mode in {0, 5}:
        body.append(_loop_sum(array_name, length, acc, mode == 5))
    elif mode in {1, 2}:
        op = ">" if mode == 1 else "<"
        body.append(_loop_if_assign(array_name, length, acc, op))
    else:
        predicate = "positive" if mode == 3 else "even"
        body.append(_loop_count(array_name, length, acc, predicate))
    body.append(Print(VarRef(acc)))
    # Keep the Python update path as an internal oracle for builder consistency.
    checked = init
    for value in values:
        checked = update(checked, value)
    assert checked == expected
    return ArrayProgram(array_name, values, body, expected_stdout=f"{expected}\n"), f"{expected}\n", f"array::len={length}::mode={mode}::name={array_name}::acc={acc}::index={index}"


def _function_array_shape(index: int) -> Tuple[FunctionArrayProgram, str, str]:
    length = index % 32 + 1
    mode = 0
    values = [((index * 5 + i * 13) % 37) - 18 for i in range(length)]
    fn_name = f"agg_{index % 127}"
    array_name = f"fa{index % 23}"
    acc = f"s{index % 29}"
    params = ["a[]", "n"]
    body: List[Any] = [VarDecl(acc, IntLiteral(values[0] if mode in {1, 2} else 0))]
    body.append(_loop_sum("a", length=None, acc=acc, doubled=index % 5 == 0, stop_name="n"))
    expected = sum(v * 2 for v in values) if index % 5 == 0 else sum(values)
    body.append(Return(VarRef(acc)))
    fn = FunctionDecl(fn_name, params, body)
    program = FunctionArrayProgram([fn], array_name, values, CallExpr(fn_name, [VarRef(array_name), IntLiteral(length)]), expected_stdout=f"{expected}\n")
    return program, f"{expected}\n", f"function_array::len={length}::mode={mode}::fn={fn_name}::acc={acc}::index={index}"


def _recursion_shape(index: int) -> Tuple[RecursiveFunctionProgram, str, str]:
    mode = index % 4
    n = index % 8 + 1
    fn_name = ("fact", "tri", "countdown", "gcd_small")[mode] + f"_{index % 97}"
    if mode == 0:
        body = [If(BinaryOp("<=", VarRef("n"), IntLiteral(1)), [Return(IntLiteral(1))], [Return(BinaryOp("*", VarRef("n"), CallExpr(fn_name, [BinaryOp("-", VarRef("n"), IntLiteral(1))])))] )]
        expected = _fact(n)
        call = CallExpr(fn_name, [IntLiteral(n)])
        params = ["n"]
    elif mode == 1:
        body = [If(BinaryOp("<=", VarRef("n"), IntLiteral(0)), [Return(IntLiteral(0))], [Return(BinaryOp("+", VarRef("n"), CallExpr(fn_name, [BinaryOp("-", VarRef("n"), IntLiteral(1))])))] )]
        expected = n * (n + 1) // 2
        call = CallExpr(fn_name, [IntLiteral(n)])
        params = ["n"]
    elif mode == 2:
        body = [If(BinaryOp("<=", VarRef("n"), IntLiteral(0)), [Return(IntLiteral(0))], [Return(CallExpr(fn_name, [BinaryOp("-", VarRef("n"), IntLiteral(1))]))] )]
        expected = 0
        call = CallExpr(fn_name, [IntLiteral(n)])
        params = ["n"]
    else:
        a = (index % 30) + 2
        b = (index * 7) % 18 + 1
        body = [If(BinaryOp("==", VarRef("b"), IntLiteral(0)), [Return(VarRef("a"))], [Return(CallExpr(fn_name, [VarRef("b"), BinaryOp("%", VarRef("a"), VarRef("b"))]))] )]
        expected = _gcd(a, b)
        call = CallExpr(fn_name, [IntLiteral(a), IntLiteral(b)])
        params = ["a", "b"]
    fn = FunctionDecl(fn_name, params, body)
    return RecursiveFunctionProgram(fn, call, max_depth=12, expected_stdout=f"{expected}\n"), f"{expected}\n", f"structured_recursion::mode={mode}::fn={fn_name}::n={n}::index={index}"


def _loop_sum(array_name: str, length: int | None, acc: str, doubled: bool, stop_name: str | None = None):
    value = ArrayRef(array_name, VarRef("i"))
    if doubled:
        value = BinaryOp("*", value, IntLiteral(2))
    return _for_loop(length, stop_name, [Assign(VarRef(acc), BinaryOp("+", VarRef(acc), value))])


def _loop_if_assign(array_name: str, length: int | None, acc: str, op: str, stop_name: str | None = None):
    value = ArrayRef(array_name, VarRef("i"))
    return _for_loop(length, stop_name, [If(BinaryOp(op, value, VarRef(acc)), [Assign(VarRef(acc), value)], [])])


def _loop_count(array_name: str, length: int | None, acc: str, predicate: str, stop_name: str | None = None):
    value = ArrayRef(array_name, VarRef("i"))
    condition = BinaryOp(">", value, IntLiteral(0)) if predicate == "positive" else BinaryOp("==", BinaryOp("%", value, IntLiteral(2)), IntLiteral(0))
    return _for_loop(length, stop_name, [If(condition, [Assign(VarRef(acc), BinaryOp("+", VarRef(acc), IntLiteral(1)))], [])])


def _for_loop(length: int | None, stop_name: str | None, body: List[Any]):
    from jianmu.extended_ir import For

    stop = VarRef(stop_name) if stop_name else IntLiteral(int(length or 0))
    return For("i", IntLiteral(0), stop, body)


def _fact(n: int) -> int:
    return 1 if n <= 1 else n * _fact(n - 1)


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def shape_hash(source: str, shape_signature: str) -> str:
    return hashlib.sha256(f"{shape_signature}\n{source}".encode("utf-8")).hexdigest()
