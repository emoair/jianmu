from dataclasses import dataclass


@dataclass
class ScoreReport:
    compile_success: int
    run_success: int
    expected_output_match: int
    consistency_check: int      # ConsistencyCheckExpert passed without error
    deterministic_replay: int
    cache_hit: int
    correctness_score: float    # compile+run+match+consistency / 4
    runtime_score: float        # deterministic_replay+cache_hit / 2
    total_score: float          # average of correctness + runtime


class Scorer:
    def score(self, sandbox_result, expected_output: str,
              previous_code: str = None, current_code: str = None,
              cache_hit: bool = False, consistency_ok: bool = True) -> ScoreReport:
        compile_success = 1 if sandbox_result.compile_success else 0
        run_success = 1 if sandbox_result.run_success else 0
        expected_output_match = 1 if sandbox_result.stdout == expected_output else 0
        consistency_check = 1 if consistency_ok else 0

        deterministic_replay = 0
        if previous_code is not None and current_code is not None:
            deterministic_replay = 1 if current_code == previous_code else 0

        cache_hit_score = 1 if cache_hit else 0

        correctness_score = (compile_success + run_success + expected_output_match + consistency_check) / 4
        runtime_score = (deterministic_replay + cache_hit_score) / 2
        total_score = (correctness_score + runtime_score) / 2

        return ScoreReport(
            compile_success=compile_success,
            run_success=run_success,
            expected_output_match=expected_output_match,
            consistency_check=consistency_check,
            deterministic_replay=deterministic_replay,
            cache_hit=cache_hit_score,
            correctness_score=correctness_score,
            runtime_score=runtime_score,
            total_score=total_score,
        )
