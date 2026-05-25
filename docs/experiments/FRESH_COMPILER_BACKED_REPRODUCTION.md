# v0.9.4.3 Fresh Compiler-Backed Reproduction

v0.9.4.3 checks whether the v0.9.4.2 patched 600/600 compiler-backed arithmetic result reproduces on fresh samples and fresh compiler invocations.

v0.9.4.2 showed that the original 45 v0.9.4.1 failures were MSVC C syntax failures caused by adjacent arithmetic tokens such as `--`. A patched replay that spaces adjacent sign tokens can make the original 600-sample set compile and run correctly, but that is still a replay of the original audit set.

Fresh reproduction is different. This version draws a new supported and boundary sample set from the audited v0.9.2 arithmetic curriculum, tracks overlap with the original 600 compiler-audit samples, requires a fresh ratio of at least 0.90, regenerates safe C source with token spacing enabled, invokes `cl.exe` through the MSVC `vcvars64` environment, runs each generated executable, and compares stdout to the expected output only after candidate generation.

Boundary samples are not compiled as supported programs. Any such route is recorded as a boundary compiler misroute.

This version does not claim solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness, or a full compiler-backed longrun.
