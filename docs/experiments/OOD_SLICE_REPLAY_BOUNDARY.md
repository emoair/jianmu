# OOD Slice Replay & Generalization Boundary（分布外切片回放与泛化边界）

## 1. Why OOD Slice Replay（为什么回放分布外切片）

v0.8.1 reported canonicalizer_made_it_look_supported（规范化器使输入看似受支持） as a major OOD false accept（分布外误接收） reason. v0.8.3 did not reproduce that reason on its new OOD precision slice.

v0.8.4 therefore replays the exact v0.8.1 OOD guard-stress（分布外守卫压力） slice where available, and separates several possibilities:

- The original issue disappeared.
- The sample slice changed.
- The detector definition changed.
- The canonicalization audit was too narrow.
- The v0.8.1 diagnostic field was a coarse heuristic.

## 2. OOD Is Not Always Toxic（OOD 不总是毒性）

Accepted OOD samples are not automatically success and not automatically toxic. They may include:

- true false accept（真正误接收）
- near-OOD generalization candidate（近邻分布外泛化候选）
- future domain candidate（未来能力候选）
- label too strict（标签过严）
- unknown（未知）

Near-OOD Generalization Candidate（近邻分布外泛化候选） entries are not treated as supported success. They enter candidate buffers for review.

## 3. Boundary Before Training（先定边界，再训练）

This version does not add near-OOD samples to supported training. It only exports candidate datasets（候选数据集） and boundary audit（边界审计） records.

The supported boundary spec（支持边界规格） keeps English arithmetic（英文算术）, decimal arithmetic（小数算术）, variable expressions（变量表达式）, equation solving（方程求解）, non-exact division（非整除）, and broader code generation outside the current supported set unless a future architecture decision changes that boundary.

## 4. Non-Claims（非主张）

This does not claim:

- stable convergence
- general program synthesis
- solved arithmetic
- AGI
- Transformer replacement
- advantage over same-size LLM
- safe real promotion
- automatic near-OOD supported success
