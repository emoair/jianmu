# Runtime Parallelism & OOD Precision Audit（运行时并行与分布外精确审计）

## 1. Why Runtime Parallelism（为什么做运行时并行）

v0.8.1.1 confirmed xlarge scale signal（确认 xlarge 规模信号）, but later 10M / 30M / 100M candidate-scale probes would be slowed by Python single-thread execution, high-frequency JSONL writes, and OneDrive-backed records I/O.

v0.8.2 does not change JianMu's main routing architecture. It keeps the same evaluation semantics and adds runtime infrastructure so the same algorithm can be evaluated more efficiently and more reproducibly.

## 2. Buffered Records（缓冲记录）

v0.8.2 uses Buffered Records（缓冲记录）:

- workers append records to memory buffers first;
- buffers flush to runtime cache shards after `buffer_size` records;
- checkpoints are written to the runtime cache after a time interval;
- final JSONL files are merged into `records/v0_8_2`;
- crashes should leave partial checkpoints rather than silently losing all progress.

The formal records directory remains the final reporting location. Runtime worker shards and checkpoints are treated as temporary execution artifacts.

## 3. OOD Precision Audit（分布外精确审计）

OOD is not assumed to be a single toxic category. v0.8.2 splits accepted OOD samples into:

- Hard OOD（硬分布外）: clearly outside scope and should be rejected;
- Near-OOD Generalization Candidate（近邻泛化候选）: unfamiliar surface form but close to the current arithmetic task;
- Future Domain Candidate（未来能力候选）: unsupported now, but plausible future extension;
- Label Too Strict（标签过严）: sample label may be more conservative than the current spec;
- True False Accept（真正误接收）: clearly outside current scope but accepted;
- Unknown（未知）: insufficient evidence for a precise label.

Canonicalization OOD Audit（规范化分布外审计） is diagnostic only. It does not modify Canonical Symbol Layer（规范符号层） logic and does not let the canonicalizer output TargetIR（目标中间表示） or C source.

## 4. Non-Claims（非主张）

This version does not claim:

- stable convergence;
- general program synthesis;
- solved arithmetic;
- AGI;
- Transformer replacement;
- advantage over same-size LLM;
- safe real promotion.

