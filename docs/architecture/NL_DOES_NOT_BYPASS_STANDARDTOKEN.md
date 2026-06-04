# NL Does Not Bypass StandardToken

v1.1-alpha keeps the substrate path explicit:

Chinese NL -> StandardToken / MirrorToken -> token-to-IR -> candidate/compiler/watchdog validation.

The adapter may not write C source, may not write raw target_ir JSON as its primary output, and may not read expected_output before candidate generation. This document is a guardrail for future NL work, not a production interface announcement.

