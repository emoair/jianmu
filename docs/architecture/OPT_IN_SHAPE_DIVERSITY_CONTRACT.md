# Opt-in Shape Diversity Contract

Shape diversity is scoped to the staged opt-in profile and remains explicit opt-in only.

Every compiled sample records a shape signature, source hash, policy, builder, IR kind, emitter, compile invocation ID, expected stdout, actual stdout, and pass flag.

Shape expansion must reuse ExtendedIR and ExtendedEmitterC. It must not introduce new production semantics or promote the staged opt-in path into the default profile.
