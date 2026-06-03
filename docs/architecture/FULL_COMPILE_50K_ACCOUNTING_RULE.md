# Full Compile 50K Accounting Rule

The 50K accounting rule separates prior clean evidence from new validation.

- Prior evidence: v0.9.27.1 clean 20K full compile validation.
- New evidence: v0.9.28.1 continuation invocations.
- Cached results must not count as new.
- Duplicate invocation ids must not count as new.
- Syntax-only checks must not count as correctness evidence.

If the new 30K is partial, the result must be marked partial and `full_compile_50k_clean` must remain false.
