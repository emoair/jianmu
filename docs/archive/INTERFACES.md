# JianMu Core Interfaces

所有接口定义为数据结构规范，不含实现。

---

## Intent

自然语言解析后的结构化意图。

```json
{
  "id": "intent-001",
  "raw_input": "计算三个整数的和",
  "operation": "sum",
  "operand_count": 3,
  "output_type": "int",
  "language": "C"
}
```

---

## ProgramIR

程序的结构化中间表示。

```json
{
  "id": "ir-001",
  "intent_id": "intent-001",
  "variables": [
    { "name": "a", "type": "int" },
    { "name": "b", "type": "int" },
    { "name": "c", "type": "int" }
  ],
  "expressions": [
    { "id": "expr-001", "op": "add", "operands": ["a", "b", "c"], "result_type": "int" }
  ],
  "statements": [
    { "type": "return", "expr_id": "expr-001" }
  ],
  "entry_function": "sum"
}
```

---

## Variable

```json
{
  "name": "a",
  "type": "int",
  "scope": "parameter"
}
```

---

## Expression

```json
{
  "id": "expr-001",
  "op": "add",
  "operands": ["a", "b", "c"],
  "result_type": "int"
}
```

---

## ExpertResult

专家处理后返回的结果。

```json
{
  "expert_id": "add-operand-expert",
  "input_ir_id": "ir-000",
  "output_ir_id": "ir-001",
  "applied_operation": "extend_add_operand",
  "success": true,
  "error": null
}
```

---

## SandboxResult

编译与运行结果。

```json
{
  "ir_id": "ir-001",
  "source_code": "#include <stdio.h>\nint sum(int a,int b,int c){return a+b+c;}\nint main(){printf(\"%d\\n\",sum(1,1,1));}",
  "compile_success": true,
  "compile_error": null,
  "run_success": true,
  "stdout": "3\n",
  "stderr": "",
  "exit_code": 0
}
```

---

## TraceCacheRecord

成功路径的缓存记录。

```json
{
  "id": "trace-001",
  "intent_id": "intent-001",
  "ir_id": "ir-001",
  "source_hash": "sha256:abc123",
  "stdout": "3\n",
  "experts_applied": ["add-operand-expert"],
  "created_at": "2026-05-18T03:00:00Z"
}
```

---

## RuntimeResult

运行时整体执行结果。

```json
{
  "intent_id": "intent-001",
  "ir_id": "ir-001",
  "trace_cache_hit": false,
  "sandbox_result": { "...": "SandboxResult" },
  "score_report": { "...": "ScoreReport" },
  "trace_saved": true
}
```

---

## ScoreReport

正确性评分报告。

```json
{
  "intent_id": "intent-001",
  "compile_success": true,
  "run_success": true,
  "expected_output": "3\n",
  "actual_output": "3\n",
  "expected_output_match": true,
  "deterministic_replay": true,
  "trace_cache_hit": false,
  "template_leak_detected": false,
  "active_expert_count": 1,
  "score": 1.0
}
```
