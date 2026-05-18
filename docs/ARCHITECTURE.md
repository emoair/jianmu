# JianMu Architecture

## 一句话定义

JianMu 是一个面向程序任务的**确定性结构化程序重写运行时**（Deterministic Structural Program Rewriting Runtime），通过自然语言意图路由、AST 级专家组合与编译器反馈验证，在极小程序域内实现可验证的组合泛化。

---

## 核心问题

当前 LLM 代码生成存在以下结构性缺陷：

- **幻觉（Hallucination）**：生成语法正确但语义错误的代码，无内联验证机制。
- **状态漂移（State Drift）**：多轮生成中上下文累积导致结构不一致。
- **长程结构不一致（Long-range Structural Inconsistency）**：复杂程序生成中局部正确但整体结构破坏。

---

## JianMu 的解决方式

```
自然语言意图
    → IntentRouter（确定性意图解析）
    → ProgramIR（结构化程序中间表示）
    → Expert 组合（原子结构专家）
    → CEmitter（C 代码生成）
    → Sandbox（gcc / clang / MSVC cl 编译 + 运行验证）
    → Scoring（正确性评分）
    → TraceCache（记录成功路径）
```

每一步均为确定性操作，编译器反馈作为内联 correctness signal，而非后处理。

---

## 系统边界

**当前 MVP 仅处理：C 语言整数求和任务。**

- 输入：自然语言描述（如"计算两个整数之和"）
- 输出：可编译、可运行、输出正确结果的 C 程序
- 验证：gcc / clang / MSVC cl 编译通过 + 运行输出与预期一致

---

## 明确非目标

- ❌ 不证明通用人工智能（AGI）
- ❌ 不替代 Transformer 或大语言模型
- ❌ 不声称通用代码智能
- ❌ 不声称可扩展至真实软件工程任务
- ❌ 不声称 O(1) 生成任意程序
- ❌ 不声称训练成本低于大模型

---

## 核心模块

| 模块 | 职责 |
|------|------|
| **IntentRouter** | 将自然语言输入解析为结构化 Intent，归一化同义表达 |
| **ProgramIR** | 程序的结构化中间表示，包含变量、表达式、语句列表 |
| **Experts** | 原子结构专家，每个专家负责一种程序结构操作（如"增加一个加法操作数"） |
| **CEmitter** | 将 ProgramIR 转换为合法 C 源代码 |
| **Sandbox** | 调用 gcc / clang / MSVC cl 编译并执行，捕获编译错误与运行输出 |
| **TraceCache** | 记录成功的 Intent→IR→Code→Output 路径，支持确定性复现 |
| **Runtime** | 协调各模块的执行流程 |
| **Scoring** | 根据编译结果、运行输出、预期值计算正确性得分 |

---

## 核心研究假设

> 若系统仅内置"两数求和"基础结构，通过专家组合能够生成"三数求和"和"四数求和"的 C 程序，并通过 supported C compiler 编译与运行验证——则说明在极小程序域内存在最小级别的 **compiler-validated compositional structural generalization**。
