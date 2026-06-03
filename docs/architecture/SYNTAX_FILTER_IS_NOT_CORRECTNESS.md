# Syntax Filter Is Not Correctness

`cl.exe /nologo /TC /WX /Zs` checks C syntax only. It does not link, execute, compare stdout, prove semantic preservation, or prove halting behavior.

The syntax frontend can remain enabled as an efficiency filter because it catches syntactic invalidity early. It must not be used as correctness evidence, readiness evidence, or production support evidence.
