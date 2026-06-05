# Symbol Binding Contract

Symbol binding samples may rename variables, functions, parameters, pointer aliases, malloc buffers, FILE handles, struct fields, and cross-file declarations only when the rename is validated against a symbol table. Unsupported or review samples must not carry trainable `target_ir` or `expected_output`.

Tokens must not contain raw C source, raw target IR JSON, or expected output. Correctness evidence comes from full compile/link/run/stdout validation, not syntax-only checks.

