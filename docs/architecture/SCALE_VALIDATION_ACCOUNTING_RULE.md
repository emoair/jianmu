# Scale Validation Accounting Rule

Scale validation must record per-sample compile invocation id, source hash, compiler invocation, link invocation, executable run, expected stdout, actual stdout, and pass/fail status. Cached, duplicate, stubbed, or summary-only validation cannot count as new real compiler evidence.

