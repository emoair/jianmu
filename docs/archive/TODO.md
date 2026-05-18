# JianMu MVP — Engineering TODO

工程 Agent 实现指南。按顺序实现，每个模块完成后运行对应测试。

---

## 模块实现顺序

### 1. ProgramIR（`src/ir.py`）
- 实现 `Variable`、`Expression`、`Statement`、`ProgramIR` 数据类
- 支持 JSON 序列化/反序列化
- 参考接口定义：`docs/INTERFACES.md`

### 2. IntentRouter（`src/intent_router.py`）
- 输入：自然语言字符串
- 输出：`Intent` 结构体
- 实现同义词归一化（两数/三数/四数求和的中英文变体）
- 不得使用外部 LLM API；使用规则/关键词匹配

### 3. Experts（`src/experts/`）
- `base_expert.py`：定义 Expert 抽象接口（`apply(ir: ProgramIR) -> ExpertResult`）
- `add_operand_expert.py`：实现"增加一个加法操作数"的原子变换
- 专家操作 IR，不得直接操作 C 源代码字符串

### 4. CEmitter（`src/c_emitter.py`）
- 输入：`ProgramIR`
- 输出：合法 C 源代码字符串
- 必须保证：相同 IR → byte-identical C 代码（无随机性）
- 生成的代码包含 `main` 函数，使用硬编码输入（1, 1, ...）验证输出

### 5. Sandbox（`src/sandbox.py`）
- 调用 `gcc` 编译生成的 C 代码（写入临时文件）
- 捕获编译错误（stderr）
- 执行编译产物，捕获 stdout/stderr/exit code
- 返回 `SandboxResult`
- 超时保护：运行超过 5 秒强制终止

### 6. Scoring（`src/scoring.py`）
- 输入：`SandboxResult` + 预期输出字符串
- 输出：`ScoreReport`
- 实现所有 `docs/EVALUATION.md` 中定义的指标计算

### 7. TraceCache（`src/trace_cache.py`）
- 存储：`TraceCacheRecord`，持久化到本地 JSON 文件（`data/trace_cache.json`）
- 查询：按 `intent_id` 或 intent 结构匹配
- 命中时直接返回缓存的 source code，跳过专家组合步骤

### 8. Runtime（`src/runtime.py`）
- 协调所有模块的完整执行流程
- 流程：IntentRouter → TraceCache 查询 → ProgramIR 构建 → Expert 组合 → CEmitter → Sandbox → Scoring → TraceCache 写入
- 返回 `RuntimeResult`

### 9. 实验脚本（`experiments/run_eval.py`）
- 按 `docs/EVALUATION.md` 定义的 E1–E7 逐一执行
- 输出每项实验的通过/失败状态
- 所有实验通过后打印 `ALL EXPERIMENTS PASSED`

---

## 测试要求

- 每个模块在 `tests/` 下有对应单元测试
- Sandbox 测试需要本机安装 `gcc`
- 运行方式：`python -m pytest tests/`

---

## 目录结构

```
jianmu-mvp/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── INTERFACES.md
│   ├── EVALUATION.md
│   ├── PAPER_OUTLINE.md
│   └── NON_CLAIMS.md
├── src/
│   ├── ir.py
│   ├── intent_router.py
│   ├── c_emitter.py
│   ├── sandbox.py
│   ├── scoring.py
│   ├── trace_cache.py
│   ├── runtime.py
│   └── experts/
│       ├── base_expert.py
│       └── add_operand_expert.py
├── experiments/
│   └── run_eval.py
├── tests/
├── data/
│   └── trace_cache.json
└── TODO.md
```

---

## 硬性约束

- ❌ 不得在 `src/` 中存储三数或四数求和的完整 C 代码模板
- ❌ 不得调用外部 LLM API
- ✅ 所有生成路径必须经过 gcc 验证
- ✅ 相同输入必须产生 byte-identical 输出
