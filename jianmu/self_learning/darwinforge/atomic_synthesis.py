from typing import Dict, Optional, Tuple

from jianmu.self_learning.branchchain.branch_types import BranchPath
from jianmu.self_learning.darwinforge.candidate import CandidateGenome, CandidatePhenotype


class AtomicSynthesis:
    def synthesize(self, genome: CandidateGenome, features: Dict) -> CandidatePhenotype:
        decisions = {decision.layer_name: decision.selected for decision in genome.branch_path.decisions}
        if genome.branch_path.early_exit or decisions.get("support_gate") == "unsupported":
            reason_parts = [
                part for part in [
                    genome.branch_path.rejected_by_layer,
                    genome.branch_path.reject_reason or genome.branch_path.unsupported_reason,
                    genome.branch_path.reject_type,
                ] if part
            ]
            return CandidatePhenotype(genome.genome_id, None, None, None, True, ":".join(reason_parts) or genome.branch_path.unsupported_reason)
        if genome.target_builder_policy != "canonical_arithmetic_targetir":
            return CandidatePhenotype(genome.genome_id, None, None, None, False, "unsupported_target_builder")
        try:
            canonical, expected = build_arithmetic_target(decisions, features)
            c_program = emit_c_program(canonical)
            return CandidatePhenotype(genome.genome_id, canonical, c_program, expected, False, None)
        except Exception as exc:
            return CandidatePhenotype(genome.genome_id, None, None, None, False, f"invalid_targetir:{type(exc).__name__}")


def build_arithmetic_target(decisions: Dict[str, str], features: Dict) -> Tuple[str, str]:
    structure = decisions.get("structure_policy")
    numbers = list(features.get("signed_numbers", []))
    ops = features.get("operator_sequence", "")
    if len(numbers) < 2 or not ops:
        raise ValueError("missing surface slots")
    if structure == "binary_operation":
        canonical, value = _binary(numbers[0], numbers[1], ops[0])
    elif structure == "reduce_chain":
        canonical, value = _reduce_chain(numbers, ops)
    elif structure == "precedence_tree":
        canonical, value = _precedence(numbers, ops)
    elif structure == "parenthesized_tree":
        canonical, value = _parenthesized(numbers, ops)
    else:
        raise ValueError(f"unsupported structure_policy: {structure}")
    return canonical, f"{value}\n"


def emit_c_program(canonical: str) -> str:
    c_expr = _canonical_to_c(canonical)
    return (
        "#include <stdio.h>\n\n"
        "int main(void) {\n"
        f"    printf(\"%d\\n\", {c_expr});\n"
        "    return 0;\n"
        "}\n"
    )


def _binary(a: int, b: int, op: str) -> Tuple[str, int]:
    if op == "+":
        return f"add(lit({a}),lit({b}))", a + b
    if op == "-":
        return f"sub(lit({a}),lit({b}))", a - b
    if op == "*":
        return f"mul(lit({a}),lit({b}))", a * b
    if op == "/":
        if b == 0 or a % b != 0:
            raise ValueError("unsupported division")
        return f"div(lit({a}),lit({b}))", int(a / b)
    raise ValueError("unknown operator")


def _reduce_chain(numbers, ops):
    node = f"lit({numbers[0]})"
    value = numbers[0]
    for i, number in enumerate(numbers[1:]):
        op = ops[min(i, len(ops) - 1)]
        if op != "+":
            raise ValueError("reduce_chain only supports addition in toy scaffold")
        node = f"add({node},lit({number}))"
        value += number
    return node, value


def _precedence(numbers, ops):
    if len(numbers) < 3 or len(ops) < 2:
        return _binary(numbers[0], numbers[1], ops[0])
    a, b, c = numbers[:3]
    pattern = ops[:2]
    if pattern == "+*":
        return f"add(lit({a}),mul(lit({b}),lit({c})))", a + b * c
    if pattern == "*+":
        return f"add(mul(lit({a}),lit({b})),lit({c}))", a * b + c
    raise ValueError("unsupported precedence pattern")


def _parenthesized(numbers, ops):
    if len(numbers) < 3 or len(ops) < 2:
        raise ValueError("parenthesized tree requires three numbers")
    a, b, c = numbers[:3]
    pattern = ops[:2]
    if pattern == "+*":
        return f"mul(add(lit({a}),lit({b})),lit({c}))", (a + b) * c
    if pattern == "-/":
        if c == 0 or (a - b) % c != 0:
            raise ValueError("unsupported parenthesized division")
        return f"div(sub(lit({a}),lit({b})),lit({c}))", int((a - b) / c)
    raise ValueError("unsupported parenthesized pattern")


def _canonical_to_c(canonical: str) -> str:
    def parse(index: int) -> Tuple[str, int]:
        if canonical.startswith("lit(", index):
            end = canonical.index(")", index)
            return canonical[index + 4:end], end + 1
        for name, op in [("add", "+"), ("sub", "-"), ("mul", "*"), ("div", "/")]:
            prefix = f"{name}("
            if canonical.startswith(prefix, index):
                left, next_index = parse(index + len(prefix))
                if canonical[next_index] != ",":
                    raise ValueError("bad canonical")
                right, next_index = parse(next_index + 1)
                if canonical[next_index] != ")":
                    raise ValueError("bad canonical")
                return f"({left} {op} {right})", next_index + 1
        raise ValueError("bad canonical")

    expr, final = parse(0)
    if final != len(canonical):
        raise ValueError("trailing canonical")
    return expr
