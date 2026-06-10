# Policy Path Map

- canonical_arithmetic_targetir -> existing arithmetic backend -> compiler/stdout
- canonical_function_targetir -> build_function_program -> FunctionCallProgram -> ExtendedEmitterC
- canonical_array_targetir -> build_array_program -> ArrayProgram -> ExtendedEmitterC
- canonical_function_array_targetir -> build_function_array_program -> FunctionArrayProgram -> ExtendedEmitterC
- canonical_structured_recursion_targetir -> build_factorial_program -> RecursiveFunctionProgram -> ExtendedEmitterC
- mixed_extended_ir_path -> deterministic mixed ExtendedIR builders -> ExtendedEmitterC
