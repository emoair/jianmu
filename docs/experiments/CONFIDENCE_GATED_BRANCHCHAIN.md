# v0.6.3 Confidence-Gated Guarded BranchChain（置信度守卫式带守卫分支链）

This document defines Confidence-Gated Guarded BranchChain（置信度守卫式带守卫分支链） for JianMu. It is a guarded-routing scaffold, not a convergence claim.

## 1. Why single support_gate is insufficient（为什么单一支持门不够）

unsupported（不支持） is not a single phenomenon.

- “写一首诗” should naturally stop near task_scope（任务范围） or another early layer.
- “calculate 1 plus 2” should stop near language_target（目标语言） or the Chinese-first（中文优先） boundary.
- “5/2” looks arithmetic on the surface and may need to reach arithmetic capability（算术能力） before rejection.

A single support_gate（支持/拒绝门） that handles every rejection becomes overloaded and can stall the BranchChain（分支链） curriculum.

## 2. Rejection as no-confidence early stop（拒绝作为无置信早停）

JianMu's primary rejection mechanism is not a single reject module.

Every BranchChain（分支链） layer has confidence-gated continuation（置信度守卫式继续）. If the current layer has no sufficiently confident continuation branch, routing stops immediately with:

```text
no_confident_branch_reject（无可信分支拒绝）
```

This means rejection is the natural result of no credible path, not a source-code patch, not a parser shortcut, and not an LLM wrapper.

## 3. Typed rejection remains optional（类型化拒绝仍可存在）

Typed rejection（类型化拒绝） may still exist:

- `reject_unsupported_language`（拒绝不支持语言）
- `reject_unknown_domain`（拒绝未知领域）
- `reject_division_by_zero`（拒绝除零）
- `reject_non_exact_division`（拒绝非整除）
- `reject_invalid_targetir`（拒绝非法 TargetIR）

However, when to use typed rejection must be learned through fitness / reward（适应度 / 奖励）, not through `expression_oracle`, `expected_output`, or target labels leaking into candidate generation.

## 4. Continue threshold（继续阈值）

Each layer has its own continue_threshold（继续阈值）.

- If `best_continue_confidence >= threshold`, continue.
- If `best_continue_confidence < threshold`, early reject.
- The threshold can be observed by Highest-Stable Threshold Search（最高稳定阈值搜索）.
- The confidence floor should not be a single hardcoded global value.

support_gate（支持/拒绝门） may remain as a compatibility layer, but it is downgraded to an ordinary BranchChain（分支链） layer. It is no longer the only rejection mechanism.

## 5. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a guarded-routing scaffold for BranchChain（分支链） training.

