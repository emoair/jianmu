# Tiny Learned Route Classifier Baseline

This v0.5.7 experiment trains a tiny pure-Python learned classifier for the
first routing layer:

```text
Chinese input_text -> route_id / task_family / supported
```

It does not generate C source code, does not generate ProgramIR tokens, and does
not replace the compiler-validated backend. The model is a multiclass
perceptron over interpretable character n-gram, keyword, numeric, punctuation,
and technical-token features.

The baseline is trained and evaluated on the controlled v0.5.6 dataset alpha.
It is intended as a comparison point for future learned router and
prefix-evolution experiments.

Non-claims:

- This does not prove general learned routing.
- This does not generate ProgramIR tokens yet.
- This does not replace the compiler-validated backend.
- This is only a tiny learned route classification baseline.
