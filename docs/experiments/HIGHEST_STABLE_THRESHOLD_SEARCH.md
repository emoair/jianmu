# v0.6.2 Highest-Stable Threshold Search（最高稳定阈值搜索）

This document defines Layerwise Highest-Stable Threshold Search（分层最高稳定冻结阈值搜索） for BranchChain（分支链） curriculum training. It is a development experiment, not a convergence claim.

## 1. Why support_gate stalls（为什么支持/拒绝门会卡住）

The v0.6.1 toy dataset has only 20 samples. One sample is a 5% swing.

- threshold `0.90` means at least `18/20` correct.
- threshold `0.85` means at least `17/20` correct.
- A single difficult supported/unsupported decision can block freezing.
- support_gate（支持/拒绝门） sits on the safety boundary between supported and unsupported paths, so it is harder than task_scope（任务范围） or language_target（语言目标）.

The stall is therefore not simply a lack of generations. Different BranchChain（分支链） layers have different difficulty.

## 2. Not lowering standards blindly（不是无脑降低标准）

This search starts each layer from a high threshold. It only anneals downward（向下退火） when the active layer stalls.

- Start from high_start threshold（高起始阈值）.
- If the layer is stable, freeze it at the current threshold.
- If it plateaus, lower the threshold by a small step.
- The frozen threshold（冻结阈值） is the highest stable threshold found so far.
- The threshold must not go below the layer floor（层级下限）.
- If the layer cannot freeze above its floor, mark it as blocked layer（阻塞层）.

## 3. Highest-Stable Threshold Search（最高稳定阈值搜索）

For each active layer:

1. start from high threshold
2. evaluate the stability window
3. if pass: freeze at current threshold
4. if plateau: `threshold -= step`
5. if threshold falls below floor: mark blocked

## 4. Integer correct count（整数正确数）

Small toy datasets should not rely only on float accuracy.

For dataset size = 20:

- threshold `0.95` -> `required_correct = 19`
- threshold `0.90` -> `required_correct = 18`
- threshold `0.85` -> `required_correct = 17`
- threshold `0.80` -> `required_correct = 16`

Reports must show threshold（阈值）, required_correct（要求正确数）, and actual_correct（实际正确数）.

## 5. layer_recall@k（层级候选召回）

winner accuracy（赢家准确率） only checks the final winning BranchPath（分支路径）.

layer_recall@k（层级候选召回） checks whether the correct branch exists among the top-k candidates.

If:

```text
winner_accuracy = 0.80
layer_recall@k = 0.95
```

then the layer can produce the correct candidate, but DarwinForge（达尔文进化炉） winner selection（赢家选择） is not good enough yet. That is a selection problem（选择问题）, not necessarily a branch generation problem.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a threshold-search scaffold for BranchChain（分支链） curriculum training.

