from jianmu.self_learning.darwinforge.turing_proof_function_array_frontend_scaleup import ARRAY_FAILURES, FUNCTION_FAILURES, TURING_FAILURES_V2


def required_failure_categories() -> dict[str, list[str]]:
    return {"function": list(FUNCTION_FAILURES), "array": list(ARRAY_FAILURES), "turing": list(TURING_FAILURES_V2)}
