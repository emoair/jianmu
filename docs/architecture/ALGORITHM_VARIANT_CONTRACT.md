# Algorithm Variant Contract

Algorithm variants are controlled surface changes over a stable semantic skeleton. A variant may change names, constants, bounds, traversal direction, helper structure, and small static dimensions, but it must keep support labels honest.

Tokens may describe the algorithm structure, but must not contain raw C source, raw target IR JSON, or expected output. Unsupported and review samples must not contain trainable `target_ir` or `expected_output`.

The corpus remains a diagnostic substrate. It is not a production runtime profile and is not evidence of arbitrary project parsing.
