# JianMu Evaluation Specification

---

## 评估指标

| 指标 | 说明 |
|------|------|
| `compile_success` | supported C compiler (gcc / clang / MSVC cl) 编译是否通过（exit code 0） |
| `run_success` | 程序运行是否正常退出（exit code 0） |
| `expected_output_match` | 运行输出是否与预期值完全一致（字符串精确匹配） |
| `deterministic_replay` | 相同 IR 重复执行，生成代码是否 byte-level 一致 |
| `trace_cache_hit` | 第二次同构任务是否命中 TraceCache |
| `template_leak_check` | 检测三数/四数求和是否由死模板直接生成（而非专家组合） |
| `active_expert_count` | 实际参与组合的专家数量（用于验证组合路径非空） |
| `generated_code_byte_identical` | 同一 intent 多次生成的 C 代码是否 byte-level 完全一致 |
| `natural_language_variant_consistency` | 同义自然语言输入是否归一化到同一 intent 结构 |

---

## 必须通过的实验

### E1：两数求和基础验证
- 输入：`"计算两个整数之和"`
- 预期输出：`2`（输入为 1, 1）
- 通过条件：`compile_success=true`, `run_success=true`, `expected_output_match=true`

### E2：三数求和组合泛化
- 输入：`"计算三个整数之和"`
- 预期输出：`3`（输入为 1, 1, 1）
- 通过条件：同 E1，且 `template_leak_check=false`，`active_expert_count >= 1`

### E3：四数求和组合泛化
- 输入：`"计算四个整数之和"`
- 预期输出：`4`（输入为 1, 1, 1, 1）
- 通过条件：同 E2

### E4：自然语言变体归一化
- 输入变体：
  - `"两数之和"`
  - `"两个数加起来"`
  - `"求两个整数的和"`
  - `"定义两个 int 并输出和"`
- 通过条件：所有变体解析到同一 `Intent`（`operation=sum`, `operand_count=2`）

### E5：确定性重放
- 操作：对同一 intent 执行两次完整流程
- 通过条件：`generated_code_byte_identical=true`, `deterministic_replay=true`

### E6：TraceCache 命中
- 操作：第一次执行 E2 后，再次执行相同 intent
- 通过条件：`trace_cache_hit=true`，输出与第一次一致

### E7：禁止死模板生成三数/四数程序
- 验证方式：系统内部不得存在三数或四数求和的完整 C 代码模板
- 通过条件：`template_leak_check=false`（通过代码审查 + 运行时路径追踪验证）

---

## 失败判定

任意一项实验未通过，则当前 MVP 验证失败，不得声称组合泛化成立。
