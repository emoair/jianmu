# Perfect-Layer Backtracking Curriculum（完美层回溯课程训练）

v0.6.7 is a toy/synthetic curriculum dynamics scaffold for BranchChain（分支链） training. It keeps the JianMu path: BranchChain（分支链） → Confidence-Gated Continuation（置信度守卫式继续） → AtomicSynthesis（原子结构合成） → TargetIR（目标中间表示） → CEmitter（C 代码发射器） → Compiler Sandbox（编译器沙箱） → DarwinForge（达尔文进化炉）.

## 1. Why Backtracking Curriculum（为什么需要回溯课程）

v0.6.1 introduced Frozen Layer（冻结层） semantics. v0.6.2 introduced Highest-Stable Threshold Search（最高稳定阈值搜索）. v0.6.3 introduced Guarded BranchChain（带守卫分支链）. v0.6.4 realigned the dataset. v0.6.5 introduced Paraphrase Group（复述组） consistency. v0.6.6 introduced Hindsight Branch Re-Ranking（回看式分支重排） and Branch Pruning（分支剪枝）.

The remaining issue is that a Downstream Layer（下游层） may fail because an Upstream Layer（上游层） froze too early or learned an unhelpful split. Continuing to train only the Active Layer（当前训练层） may not fix that. v0.6.7 therefore allows Layer Backtracking（层级回溯）: conditionally unfreeze the current layer and a small upstream window, then retrain them jointly.

## 2. Perfect Layer Assumption（完美层假设）

In a toy/synthetic deterministic dataset（玩具/合成确定性数据）, labels are noise-free, sample count is small, and the target BranchChain（分支链） path is deterministic. In this narrow setting, each layer can attempt 100% layer accuracy（分层准确率） before freezing.

This is a toy-only assumption. Larger or noisy datasets must return to Highest-Stable Threshold Search（最高稳定阈值搜索） instead of requiring 100%.

## 3. Frozen Does Not Mean Dead（冻结不是死亡）

A Frozen Layer（冻结层） still:

- participates in routing（参与路由）
- emits BranchDecision（输出分支决策）
- contributes confidence（贡献置信度）
- can be conditionally unfrozen（可条件解冻）

Frozen only means:

- no mutation（不扰动）
- no normal score update（不做普通分数更新）

## 4. Backtracking Rule（回溯规则）

If the Active Layer（当前训练层） does not reach the perfect threshold within patience generations:

1. unfreeze the Active Layer（当前训练层）
2. unfreeze the previous N Upstream Layer（上游层） entries
3. mark the window as Backtracking Curriculum（回溯课程）
4. jointly train for a bounded number of generations
5. re-freeze if the downstream layer improves
6. mark blocked_layer（阻塞层） if repeated attempts fail

## 5. 100% vs Highest Stable（100% 与最高稳定阈值）

Toy mode:

- perfect_accuracy_required = True
- required_correct = total_count

Future large-data mode:

- use Highest-Stable Threshold Search（最高稳定阈值搜索）
- do not require 100%

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a toy/synthetic curriculum dynamics scaffold.
