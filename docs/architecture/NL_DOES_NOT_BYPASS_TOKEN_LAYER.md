# NL Does Not Bypass Token Layer

The LinguaForge adapter is a bounded normalization layer. It cannot call compiler validation, generate C source, generate target_ir JSON, or steer candidate generation directly from natural language. All supported paths go through ProjectToken, AlgorithmToken, CSystemsToken, or SymbolBindingToken.
