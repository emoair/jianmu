# CRITIQUE.md — JianMu 红队审查报告

**审查日期：** 2026-05-18
**审查立场：** 严格红队，不为项目背书，不圆谎

---

## 逐条审查（14 问）

### 1. 项目是否把三数/四数求和写成了死模板？

✅ **已修复（变量值硬编码问题）**

`VariableDefinitionExpert(n)` 动态生成 n 个变量，`ExpandSumExpert(target)` 动态追加 operands，没有发现 `generate_three_sum_template` 或 `generate_four_sum_template` 这类硬编码函数。结构上不是死模板。

变量值硬编码为 `1` 的问题已在 v0.3 修复：`IntentRouter` 现在从用户输入中提取 `values` 参数，`VariableDefinitionExpert` 接受 `values` 参数并按实际值生成变量声明，`ExpandSumExpert` 接受 `new_value` 参数支持追加指定值的变量。系统现在可以生成 `1+2+3=6` 这类非平凡求和，correctness signal 具有真实区分度。

已支持有限数值泛化，但不支持负数、零、复杂表达式。

---

### 2. 所谓泛化是否只是 if-else 伪装？

⚠️ **有瑕疵**

`IntentRouter` 是纯正则/关键词匹配，`_parse_target_num` 优先匹配"改成/变成/扩展成"后的数字。这不是 if-else 死分支，但覆盖范围极窄。

"把两数求和扩展成三数" → 可以命中。
"我想要三个变量相加" → 大概率失败。

泛化的是 IR 结构组合，不是自然语言理解。这个边界项目自己承认了（non-claims），但 README 的措辞仍可能给读者造成误导。

---

### 3. ProgramIR 是否真的存在，还是只是字符串拼接？

✅ **通过（IR 存在）** / ⚠️ **Emitter 有瑕疵**

`ir.py` 中 `Variable`、`SumExpression`、`ProgramIR` 是真实的 dataclass，支持 `to_dict/from_dict`，IR 作为独立数据结构存在于内存和缓存中。

但 `emitter_c.py` 是字符串拼接生成 C 代码，不是 AST rewrite。这意味着：
- IR → C 的转换没有经过语法树验证
- 如果 IR 结构出现边界情况（如空 operands），emitter 可能静默生成语法错误的 C 代码
- 无法做 AST 级别的变换或优化

IR 存在，但 IR 到代码的桥梁是脆弱的字符串操作。

---

### 4. Expert 是否真的是原子结构操作？

⚠️ **有瑕疵**

三个 Expert 职责划分基本清晰：
- `VariableDefinitionExpert`：只管变量声明
- `ExpandSumExpert`：只管 operands 追加
- `ConsistencyCheckExpert`：只管引用完整性检查

但 `ExpandSumExpert` 存在单向性问题：只能扩展（增加变量），不能缩减。`target < current` 的情况未处理。这不是"原子操作"，而是"单向原子操作"，缺少逆操作使其不完备。

此外，`ExpandSumExpert` 在 `previous_ir=None` 时的降级行为没有测试覆盖，行为未知。

---

### 5. 三数/四数是否真的由变量专家 + 求和表达式专家组合生成？

✅ **通过**

根据 `experts.py` 的实现，三数和四数走相同的专家路径，只是 `n` 参数不同：
- `VariableDefinitionExpert(3)` vs `VariableDefinitionExpert(4)`
- `ExpandSumExpert(3)` vs `ExpandSumExpert(4)`

这是真实的参数化组合，不是两条独立代码路径。这一点是项目最强的结构证据。

---

### 6. 所有输出是否真的经过 gcc/clang 编译？

✅ **通过**

`sandbox.py` 使用 `subprocess + tempfile`，调用真实 `gcc/clang`，有 timeout 保护。没有发现 mock 编译或伪造输出的路径。

---

### 7. 是否存在没编译却声称成功的路径？

⚠️ **有瑕疵**

`runtime.py` 在 cache hit 时：重新编译运行（不直接返回缓存结果），但 `generated_code` 直接返回缓存中的代码字符串，不重新生成。

这意味着：cache hit 路径下，代码字符串来自缓存，编译的是缓存代码。如果缓存代码与"重新生成的代码"不一致（理论上不应该，但 `deterministic_replay` 的 bug 使这一保证未被验证），则存在"编译了 A，但声称生成了 B"的潜在风险。

目前没有发现"声称成功但实际未编译"的路径，但上述逻辑漏洞使这一保证依赖于 emitter 的确定性，而非显式验证。

---

### 8. Trace Cache 是否真的命中？

✅ **通过（机制正确）** / ⚠️ **验证逻辑有缺陷**

`trace_cache.py` 使用 `sha256(intent + prev_ir)` 作为 key，JSON 持久化，机制本身正确。

但 `scoring.py` 的 `deterministic_replay` 只比较 `stdout == expected_output`，没有比较 `generated_code` 字符串本身。这意味着 cache 命中的"一致性"只被 stdout 间接验证，不是 byte-level 代码一致性验证。

测试 `test_deterministic_replay` 通过 cache hit 验证代码一致性，但这只是因为 cache 存了代码字符串并直接返回，不是"重新生成后比较"——这是循环论证，不是真正的 determinism 证明。

---

### 9. deterministic replay 是否 byte-level 一致？

✅ **已修复**

`scoring.py` 的 `score()` 现在接受 `previous_code` 和 `current_code` 参数，并显式执行 `current_code == previous_code` 的字符串比较。byte-level 代码一致性现在有代码支撑，不再仅依赖 stdout 间接验证。emitter 若引入非确定性（时间戳注释、随机变量名等），`deterministic_replay` 会直接检测到。

---

### 10. 自然语言变体是否真的归一化到结构 intent？

⚠️ **有改善但仍有限**

`IntentRouter` 新增了以下覆盖范围：
- 英文支持："sum of three numbers" 现在可命中（支持 three/numbers 关键词）
- 中文数字列举："1加2加3" 可解析并提取 values
- 追加变体："多加一个X" 可解析并提取 new_value
- 新关键词："扩展为" 作为触发词

仍然存在的局限：
- "三个整数相加"、"add one more variable"、"extend to include d" 等变体仍无法处理
- 任意英文自然语言表达仍会失败，已支持英文 three/numbers 关键词，但覆盖依赖枚举正则
- 覆盖依赖枚举正则，不是真正的 NLU，无法泛化到未见过的表达方式
- 没有 benchmark 数据支撑覆盖率声明

这不是"自然语言归一化"，仍然是"扩展后的有限关键词匹配"。项目在 non-claims 中承认了这一点，但论文措辞仍需谨慎，reviewer 会要求展示系统性的变体鲁棒性测试。

---

### 11. README 是否过度声称？

⚠️ **有瑕疵**

README 的 non-claims 部分存在遗漏：
- 未明确声明"不证明真正自然语言通用理解"
- 未明确声明"不证明万 CPU 硬件架构可行"

现有 non-claims 覆盖了"不替代 LLM/编译器/通用程序合成"，但对"自然语言理解"的边界描述不够清晰。读者可能误解 IntentRouter 具有真实 NLU 能力。

---

### 12. 当前结果能证明什么？

在以下严格限定条件下，项目的证明是有效的：

- **极小程序域**（C 整数求和）内，结构组合泛化是真实的
- 三数/四数由相同专家路径参数化生成，不是死模板
- 编译执行反馈是真实的（真实 gcc/clang）
- Trace Cache 机制正确，key 设计合理
- IR 作为独立数据结构存在，与代码生成解耦
- 已支持有限数值泛化（如 1+2+3=6），correctness signal 具有真实区分度

---

### 13. 当前结果不能证明什么？

- **不能证明**完整数值泛化：已支持有限数值泛化，但不支持负数、零、复杂表达式
- **不能证明**自然语言通用理解：IntentRouter 是关键词匹配，任意自然语言仍会失败
- **不能证明**缩减操作（target < current）：ExpandSumExpert 单向
- **不能证明**通用程序合成、大规模软件工程有效性
- **不能证明**替代 LLM 或编译器
- **不能证明**万 CPU 硬件架构可行

---

## Reviewer 最可能攻击的 5 个点

### R1. 变量值硬编码为 1，求和验证无意义 [已修复]

v0.3 已修复：`IntentRouter` 提取 `values`，`VariableDefinitionExpert` 按实际值初始化变量，系统可正确生成并验证 `1+2+3=6`。已支持有限数值泛化，但不支持负数、零、复杂表达式，这些场景仍需后续扩展。

### R2. deterministic_replay 的实现与声明不符 [已修复]

v0.3 已修复：`scoring.py` 的 `score()` 现在接受 `previous_code` / `current_code` 参数并做字符串比较，byte-level 一致性有代码支撑，不再仅依赖 stdout 间接验证。

### R3. IntentRouter 不是 NLU，是关键词匹配

如果论文在任何地方使用"natural language"、"intent understanding"或类似措辞，reviewer 会要求展示对自然语言变体的鲁棒性测试。已支持英文 three/numbers 关键词，但任意英文自然语言表达仍会失败。这使得"自然语言 → 结构 intent"的 pipeline 描述仍具有一定误导性。

### R4. 泛化范围过窄，无法支撑任何规模声明

系统只在"整数求和，变量数 2→3→4"这一条路径上被验证。没有乘法、减法、括号、不同数据类型、不同变量名。Reviewer 会问：这个"泛化"是否只是对一个参数（变量数量）的线性外推？如果是，它与硬编码三个模板的区别在哪里？

### R5. 测试设计存在循环论证

`test_deterministic_replay` 通过 cache hit 验证代码一致性，但 cache 本身存储了代码字符串并直接返回——这不是"重新生成后比较"，而是"返回缓存后与缓存比较"。这个测试证明的是"cache 读写正确"，不是"生成过程是确定性的"。论文中任何关于 determinism 的声明都需要一个真正的端到端重新生成测试来支撑。

---

*本报告基于已知代码事实，不基于假设。所有结论均可在对应源文件中验证。*

---

## 修复记录

### v0.3 已修复

- **变量值硬编码**：`IntentRouter` 提取 `values`，`VariableDefinitionExpert` 接受 `values` 参数按实际值生成变量声明，`ExpandSumExpert` 接受 `new_value` 参数支持追加指定值的变量。系统可生成 `1+2+3=6` 等非平凡求和，已支持有限数值泛化，但不支持负数、零、复杂表达式。
- **deterministic_replay bug**：`scoring.py` 的 `score()` 现在接受 `previous_code` / `current_code` 参数并做字符串比较，byte-level 一致性有代码支撑。
- **ExpandSumExpert 单向**：`new_value` 参数支持追加指定值的变量，语义不再锁死为全 1。
- **IntentRouter 覆盖扩展**：新增英文支持（"sum of three numbers"，支持 three/numbers 关键词）、"1加2加3" 解析、"多加一个X" 解析、"扩展为" 关键词。任意英文自然语言表达仍会失败。

### 仍然存在

- **CEmitter 字符串拼接**：`emitter_c.py` 仍是字符串拼接生成 C 代码，非 AST rewrite，边界情况可能静默生成语法错误代码。
- **IntentRouter 非真正 NLU**：覆盖依赖枚举正则，无法泛化到未见过的自然语言表达，不是真实意图理解。
- **无 benchmark**：没有系统性的变体覆盖率测试数据，所有"支持"声明均为枚举而非统计。
- **数值泛化有限**：不支持负数、零、多位数、中文顿号/逗号分隔等场景。
