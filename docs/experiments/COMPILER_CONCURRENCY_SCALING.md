# v0.9.5.1 Compiler Concurrency Scaling

v0.9.5.1 measures how MSVC `cl.exe` concurrency affects compiler-backed arithmetic validation throughput.

v0.9.5 already established a bounded real compiler-backed arithmetic longrun with per-sample traces, boundary guards, and no compiler verification failures. This version does not test a new capability. It varies the number of concurrent compiler tasks while keeping the Python process as a lightweight orchestrator.

`python_worker_count` controls orchestration. `compile_worker_count` controls how many supported arithmetic samples may be compiled and executed concurrently through real `cl.exe` subprocesses. This distinction matters: the probe is about compiler process throughput, startup cost, temporary file IO, latency, and system stability, not about opening hundreds of independent Python main processes.

Real compiler invocation means generating safe C source, invoking MSVC `cl.exe`, running the generated executable, and comparing stdout to the expected output only after candidate generation. Internal evaluator execution, Python subprocess execution, cached result replay, and summary-only metrics do not count.

This version does not claim solved arithmetic, stable convergence, solved OOD, same-size LLM advantage, safe real promotion, production readiness, or Turing completeness.
