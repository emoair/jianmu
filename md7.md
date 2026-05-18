你现在基于 JianMu v0.3 clean baseline 开发 v0.4。

非常重要：不要继续把项目做成“正则自然语言计算器”。v0.3 已经证明了 ProgramIR + Expert + CEmitter + GCC Sandbox 的执行后端能跑，但它还不是 JianMu 主体。

v0.4 的目标不是扩展更多运算符，而是实现 JianMu 的核心运行机制：

多候选路由
→ 投机执行
→ 编译/运行反馈裁决
→ 路径记忆
→ 下次相似输入优先选择历史成功路径

当前问题：

v0.3 的 IntentRouter 本质是规则/正则直接拍板：

自然语言
→ 单一 intent
→ 固定专家链
→ 生成代码

这不是真正 JianMu。真正 JianMu 不能让正则直接决定答案。正则最多只能生成候选路径，最终路径必须由执行反馈裁决。

请严格按以下目标修改。

==================================================
一、核心目标
==================================================

把当前 Runtime 从：

user_input
→ single intent
→ single expert chain
→ one generated program
→ compile/run

升级为：

user_input
→ multiple RouteCandidate
→ each candidate generates ProgramIR/code
→ each candidate is compiled and executed
→ each candidate receives ExecutionScore
→ best candidate is selected
→ successful route is written into RouteMemory/QTable
→ next similar input uses historical route priority

这叫 JianMu v0.4: Speculative Execution Routing Runtime。

==================================================
二、禁止事项
==================================================

1. 不要继续堆更多正则来直接输出最终答案。
2. 不要把 v0.4 做成自然语言计算器。
3. 不要引入外部 LLM API。
4. 不要重写整个项目。
5. 不要破坏 v0.3 既有 29 个测试。
6. 不要写死完整三数/四数程序模板。
7. 不要声称 AGI、替代 Transformer、替代编译器。
8. 不要让 IntentRouter 直接决定最终路径。
9. 不要让 TraceCache 替代 RouteMemory。TraceCache 记录成功结果，RouteMemory 记录路径经验，它们不是一回事。

==================================================
三、新增核心概念
==================================================

请新增这些模块，文件名可以按项目风格调整：

jianmu/routes.py
jianmu/speculative_router.py
jianmu/route_memory.py
jianmu/candidate_executor.py

或者如果你认为合适，也可以合并进现有文件，但结构必须清晰。

--------------------------------------------------
1. RouteCandidate
--------------------------------------------------

定义数据结构：

RouteCandidate:
- route_id: str
- source: str
  例如 "rule_candidate", "memory_prior", "fallback"
- intent: dict
- expert_plan: list[str]
- prior_score: float
- requires_previous_ir: bool
- expected_output: optional[str]
- rationale: str

注意：

prior_score 不是最终分数。
prior_score 只是先验排序。
最终赢家由编译/运行/expected_output/consistency 反馈决定。

--------------------------------------------------
2. CandidateExecutionResult
--------------------------------------------------

定义：

CandidateExecutionResult:
- candidate: RouteCandidate
- program_ir
- generated_code
- sandbox_result
- score_report
- success: bool
- final_score: float
- errors: list[str]

--------------------------------------------------
3. RouteMemory / QTable
--------------------------------------------------

新增 route_memory.json 或类似机制。

它记录：

key = normalized semantic situation

value:
- route_id
- success_count
- failure_count
- avg_score
- last_success_code_hash
- last_updated

它不是 TraceCache。

TraceCache:
- 记录某个具体 intent + program_state 的最终代码结果。

RouteMemory:
- 记录某类输入下哪条 route 更容易成功。

要求：

- 成功路径增加 success_count
- 失败路径增加 failure_count
- avg_score 更新
- 下次生成 candidates 时，同类输入中历史成功 route 的 prior_score 应提高

--------------------------------------------------
4. SpeculativeRouter
--------------------------------------------------

SpeculativeRouter 不直接返回一个 intent。
它返回多个 RouteCandidate。

例如输入：

“让程序多加一个 2”

如果 previous_ir 存在，必须产生至少以下候选：

Candidate A:
route_id = "append_literal_to_existing_sum"
intent = {
  "action": "expand_sum_program",
  "mode": "append_literal",
  "value": 2
}
expert_plan = ["ExpandSumExpert", "ConsistencyCheckExpert"]
prior_score = 0.6

Candidate B:
route_id = "generate_new_sum_from_text"
intent = {
  "action": "generate_sum_program",
  "values": [2]
}
expert_plan = ["VariableDefinitionExpert", "SumExpressionExpert", ...]
prior_score = 0.3

Candidate C:
route_id = "replace_last_operand"
intent = {
  "action": "replace_last_operand",
  "value": 2
}
expert_plan = ["ReplaceOperandExpert", "ConsistencyCheckExpert"]
prior_score = 0.2

然后 Runtime 分别执行候选，编译运行，按结果选赢家。

如果 previous_ir 不存在，append_literal_to_existing_sum 应该失败或降低 prior，不应该直接成功。

--------------------------------------------------
5. CandidateExecutor
--------------------------------------------------

负责执行一个 RouteCandidate：

RouteCandidate
→ 调用对应专家链
→ 生成/修改 ProgramIR
→ CEmitter 生成代码
→ ConsistencyCheck
→ Sandbox 编译运行
→ Scoring
→ 返回 CandidateExecutionResult

要求：

- 每个候选都必须真实走 ProgramIR + CEmitter + Sandbox
- 失败候选也要有结构化错误
- 不能只执行 prior_score 最高的候选
- 默认至少执行 top_k=3 个候选，除非候选不足

--------------------------------------------------
6. Runtime 选择逻辑
--------------------------------------------------

Runtime.run(...) 需要支持 speculative=True。

流程：

1. SpeculativeRouter.generate_candidates(user_input, previous_ir)
2. RouteMemory 调整候选 prior_score
3. 按 prior_score 排序
4. 执行 top_k 候选
5. 每个候选得到 final_score
6. 选择 final_score 最高且 correctness_score == 1.0 的候选
7. 若没有完全正确候选，返回最佳失败结果和错误列表
8. 更新 RouteMemory:
   - winner success_count +1
   - losers failure_count +1
9. 只有 winner correctness_score == 1.0 时才写 TraceCache
10. 返回 RuntimeResult，必须包含：
   - all_candidates
   - executed_candidates
   - selected_candidate
   - rejected_candidates
   - route_memory_updates
   - generated_code
   - sandbox_result
   - score_report
   - cache_hit

==================================================
四、必须新增的行为测试
==================================================

新增 tests/test_speculative_routing.py。

至少包含以下测试。

--------------------------------------------------
1. test_router_generates_multiple_candidates_for_ambiguous_append
--------------------------------------------------

输入：

previous_ir = 两数 1+1 程序
user_input = "让程序多加一个 2"

要求：

SpeculativeRouter 至少产生 3 个候选：
- append_literal_to_existing_sum
- generate_new_sum_from_text
- replace_last_operand

不能只返回一个 intent。

--------------------------------------------------
2. test_speculative_execution_selects_correct_append_route
--------------------------------------------------

场景：

previous_ir = 1 + 1
user_input = "让程序多加一个 2"
expected_output = "4\n"

候选中：
- append_literal_to_existing_sum 应生成 1+1+2，输出 4，成功
- generate_new_sum_from_text 可能输出 2，不应胜出
- replace_last_operand 可能输出 1+2，不应胜出

要求 selected_candidate.route_id == "append_literal_to_existing_sum"。

--------------------------------------------------
3. test_failed_candidates_are_recorded
--------------------------------------------------

执行上面场景后，RouteMemory 中：

- winner success_count >= 1
- 至少一个 loser failure_count >= 1

--------------------------------------------------
4. test_route_memory_increases_prior_for_successful_route
--------------------------------------------------

第一次执行 “让程序多加一个 2” 后，append_literal_to_existing_sum 成功。

第二次对相似输入：

“再加一个 3”

生成 candidates 时，append_literal_to_existing_sum 的 prior_score 必须高于初始默认值，或者排序更靠前。

--------------------------------------------------
5. test_no_single_intent_shortcut
--------------------------------------------------

验证 Runtime 在 speculative=True 时，不允许 IntentRouter 直接返回单个 intent 并跳过候选执行。

必须确认 executed_candidates 数量 >= 2。

--------------------------------------------------
6. test_no_cache_write_for_losing_candidates
--------------------------------------------------

失败候选不能写入 TraceCache。
只有 selected winner 且 correctness_score == 1.0 才能缓存。

--------------------------------------------------
7. test_previous_ir_required_for_append_route
--------------------------------------------------

如果 previous_ir=None：

输入 “让程序多加一个 2”

append_literal_to_existing_sum 不能成功。
系统可以选择 generate_new_sum_from_text 或返回结构化错误。

--------------------------------------------------
8. test_route_memory_is_not_trace_cache
--------------------------------------------------

确认：
- TraceCache 保存最终代码结果
- RouteMemory 保存 route_id 的 success/failure 经验
两者文件和语义分开。

--------------------------------------------------
9. test_deterministic_candidate_generation
--------------------------------------------------

相同 input + same previous_ir + same route_memory 状态下，候选列表顺序和 route_id 必须一致。

--------------------------------------------------
10. test_speculative_result_contains_full_audit_trail
--------------------------------------------------

RuntimeResult 必须包含：

- all_candidates
- executed_candidates
- selected_candidate
- rejected_candidates
- route_memory_updates

这是论文和红队审查需要的证据链。

==================================================
五、保留 v0.3 能力
==================================================

所有原 tests 必须继续通过。

特别是：

- 两数求和
- 三数求和
- 四数求和
- 1+2+3 -> 6
- TraceCache hit
- wrong expected output not cached
- deterministic replay
- no hardcoded templates

==================================================
六、文档更新
==================================================

更新 README.md：

必须明确写：

JianMu v0.3 是 deterministic ProgramIR execution scaffold。
JianMu v0.4 新增 speculative routing：

一个输入不再直接映射到单一路径，而是产生多个候选路径，并由编译/运行反馈裁决。

当前 v0.4 仍然不证明：
- 真正自然语言理解
- 大规模泛化
- 自主学习通用程序
- BPU 硬件共生
- AGI

当前 v0.4 证明：
- 可以把规则 router 从“最终裁决者”降级为“候选生成器”
- 多候选专家链可以通过真实执行反馈选择正确路径
- RouteMemory 可以记录路径级经验并影响后续 prior
- TraceCache 与 RouteMemory 可以分工：一个缓存结果，一个缓存路径经验

新增 docs/SPECULATIVE_ROUTING.md，说明：

- 为什么 v0.3 还不是 JianMu 主体
- v0.4 如何接近 JianMu 主体
- RouteCandidate
- CandidateExecutor
- Execution feedback
- RouteMemory/QTable
- TraceCache vs RouteMemory
- 当前限制

更新 CRITIQUE.md：

必须诚实写：

v0.4 仍然是小域规则候选生成，不是真正 learned router。
但它已经具备 JianMu 所需的核心 runtime 形状：
- 多路径
- 投机
- 执行裁决
- 路径记忆

==================================================
七、records 和版本
==================================================

不要修改 records/v0.3 的内容。

完成后新增：

records/test_v0.4.txt
records/V0_4_BASELINE.md

V0_4_BASELINE.md 内容包括：

- 新增 speculative routing
- 新增 RouteMemory
- 新增多候选执行
- 新增测试数量
- 当前仍未实现 learned router
- 当前仍未实现硬件级 BPU 共生

==================================================
八、验收命令
==================================================

完成后必须运行：

python -m pytest tests/ -v

如果失败，不要掩盖，修到通过。

最后输出：

1. 新增文件
2. 修改文件
3. 新增测试数量
4. 总测试数量
5. pytest 结果
6. v0.4 现在证明了什么
7. v0.4 仍然没有证明什么
8. 是否可以 commit/tag v0.4

==================================================
九、最终提醒
==================================================

这次不要把项目做成“更复杂的正则计算器”。

目标不是识别更多说法。
目标是让同一句话产生多个候选结构路径，并让执行反馈而不是正则规则来裁决路径胜负。

正则只能负责提出候选。
编译器和运行结果才是法官。