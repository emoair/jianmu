# LinguaForge NL Adapter Contract

LinguaForge is an alpha adapter. Its output contract is token-only: Chinese NL may produce StandardToken or MirrorToken, and later stages may reconstruct supported-substrate IR through the existing token path.

The adapter is not a verifier. Compiler/watchdog validation remains the final supported-output judge. Boundary-as-Data-Contract remains intact: unsupported, future-domain, and review samples are isolated by dataset labels and audits rather than runtime keyword rejection gates.

Forbidden paths:

- NL directly to C
- NL directly to target_ir
- NL bypassing StandardToken or MirrorToken
- NL output treated as truth
- production default profile change

