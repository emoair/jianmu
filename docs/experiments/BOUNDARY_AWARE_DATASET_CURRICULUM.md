# Boundary-Aware Dataset Curriculum（边界感知数据课程）

## 1. Why Boundary-Aware Dataset（为什么重做边界感知数据集）

v0.8.4 showed that accepted OOD（分布外） samples were mostly Future Domain Candidate（未来能力候选）, Hard OOD（硬分布外）, and True False Accept（真正误接收） cases, not immediate supported expansion.

The rejection gate（拒绝门） should not be hand-coded. v0.8.5 builds a Boundary-Aware Dataset Curriculum（边界感知数据课程） so rejection behavior can later emerge from Nutrient / Toxic Pressure（养分 / 毒性压力） instead of keyword rules.

## 2. Dataset Boundary Labels（数据集边界标签）

- current_supported（当前支持）
- hard_ood（硬分布外）
- true_false_accept_trap（真正误接收陷阱）
- future_domain_candidate（未来能力候选）
- near_ood_generalization_candidate（近邻泛化候选）
- label_review_candidate（标签复审候选）

## 3. Nutrient / Toxic Pressure（养分 / 毒性压力）

- current_supported correct accept = positive nutrient（正养分）
- current_supported false reject = toxic（毒性）
- hard_ood false accept = strong toxic（强毒性）
- hard_ood correct reject = positive nutrient（正养分）
- true_false_accept_trap accept = strong toxic（强毒性）
- future_domain_candidate current accept = neutral / weak toxic（中性 / 弱毒性）, not positive
- future_domain_candidate current reject = neutral / weak positive（中性 / 弱正养分）
- near_ood_generalization_candidate = candidate buffer（候选缓冲区）, not immediate supported
- label_review_candidate = no training label change（不改变训练标签）

## 4. Scale Expansion（规模扩展）

This version supports:

- small sanity（小型 sanity）
- medium（中型）
- large（大型）
- xlarge candidate（超大型候选）

Each scale records sample distribution, duplicate rate, leakage checks, and boundary conflicts.

## 5. Non-Claims（非主张）

This does not claim:

- stable convergence
- general program synthesis
- solved arithmetic
- AGI
- Transformer replacement
- advantage over same-size LLM
- safe real promotion
- OOD solved
