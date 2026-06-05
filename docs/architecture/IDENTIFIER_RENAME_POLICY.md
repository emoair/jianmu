# Identifier Rename Policy

Identifier rename must preserve scope, binding identity, and header/source consistency. It must not mutate string literals, comments, unrelated identifier substrings, or macro-like text without an explicit contract.

Shadowed locals, struct fields, parameters, globals, static helpers, file handles, malloc buffers, and pointer aliases are separate binding objects even when their surface names overlap.

