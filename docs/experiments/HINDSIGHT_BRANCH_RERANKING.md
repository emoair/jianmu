# Hindsight Branch Re-Ranking（回看式分支重排）

v0.6.6 adds a scaffold for Hindsight Branch Re-Ranking（回看式分支重排）, Group Beam Selection（组级束搜索）, and Branch Pruning（分支剪枝）. It does not change the JianMu path: BranchChain（分支链） → Confidence-Gated Continuation（置信度守卫式继续） → AtomicSynthesis（原子结构合成） → TargetIR（目标中间表示） → CEmitter（C 代码发射器） → Compiler Sandbox（编译器沙箱） → DarwinForge（达尔文进化炉）.

## 1. Why Re-Ranking（为什么需要重排）

v0.6.5 evaluates Paraphrase Group（复述组） consistency, but it still chooses a single-sample winner before group feedback. If the correct BranchPath（分支路径） has a low initial score, it can be discarded too early.

The v0.6.6 training shape is:

top-k candidate retention（保留前 k 个候选） → hindsight evaluation（回看式评估） → branch re-ranking（分支重排） → pruning high-score wrong shortcuts（剪枝高分错误捷径）

## 2. Candidate Quadrants（候选四象限）

Candidate paths are classified into four quadrants:

1. high-score-correct（高分且正确）: reinforce.
2. high-score-wrong（高分但错误） / Wrong-High-Score Candidate（高分错误候选）: downrank or mark as a pruning candidate（剪枝候选）.
3. low-score-correct（低分但正确） / Correct-Low-Score Candidate（低分正确候选）: promote through rerank bonus（重排奖励）.
4. low-score-wrong（低分且错误）: discard or keep only for exploration.

## 3. Group Beam Selection（组级束搜索）

For each Paraphrase Group（复述组）:

- every sample keeps top-k candidates;
- candidates are re-ranked with TargetIR（目标中间表示） and expected_output feedback after prediction;
- group hypotheses are built from candidate TargetIR outputs;
- the selected group beam should prioritize TargetIR exact match（目标中间表示精确匹配）, Group Consistency（组内一致性）, Cross-Mode Consistency（跨输入模式一致性）, low collapse（低坍缩）, and correct OOD Evaluation（分布外评测） rejection.

## 4. Correctness Over Consistency（正确性高于一致性）

Consistently wrong output is not success.

If the `add_mul_1_2_3` group should produce:

`add(lit(1),mul(lit(2),lit(3)))`

but every paraphrase produces:

`add(lit(1),lit(2))`

then Group Consistency（组内一致性） is high, but TargetIR exact match（目标中间表示精确匹配） is false. This is wrong-consistent collapse（错误一致坍缩） and must be penalized.

## 5. Re-Ranking and Pruning（重排与剪枝）

Low-score-correct candidates（低分正确候选） receive a rerank bonus（重排奖励）. High-score-wrong candidates（高分错误候选） receive a pruning penalty（剪枝惩罚） or are recorded as prunable shortcuts（可剪枝捷径）.

Re-ranking does not hard-code the final answer. It adjusts branch weights, score_value, and replay priority after prediction. Branch Pruning（分支剪枝） does not permanently delete all wrong paths in this scaffold; it records them for downranking, mutation away, or continued exploration.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a hindsight branch re-ranking scaffold.
