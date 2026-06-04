# Agent Reliability Lab 项目说明

## 项目定位

Agent Reliability Lab 是一个面向 LLM Agent 的轻量级评估、可观测性和回归测试工具。它的目标不是再做一个聊天机器人 demo，而是解决 agent 工程里更实际的问题：

```text
agent 每次运行为什么变了？
prompt 或模型换了之后哪里退化了？
工具调用是否正确？
RAG 回答是否有证据支撑？
有没有隐私或安全违规？
这些行为能不能自动回归测试？
```

这个项目适合作为实习简历项目，因为它覆盖了 agent 岗位常见要求：LLM agent 构建、RAG、tool use、evaluation、observability、safety、FastAPI、SQLite、dashboard 和 CI。

## 项目边界

这是一个独立的通用 agent 工程工具，不涉及任何桌宠、人设、proactive companion、用户长期状态或私有项目设定。

公开描述时只说：

```text
LLM Agent evaluation
agent observability
trace / replay / diff
RAG evaluation
tool-call reliability
regression testing
safety checks
```

不要提：

```text
桌宠
MemoPet
proactive agent 主项目
mind-wandering
homeostatic proactivity
真实用户记忆 schema
当前项目 benchmark
```

## 核心功能

### 1. Docs QA Agent

一个基于本地文档的 RAG agent。

输入：

```text
用户问题
本地 markdown/txt 文档
```

输出：

```text
回答
引用的文档片段
是否 grounded
```

要记录：

```text
query
retrieved_chunks
prompt
answer
citations
latency
token usage
```

### 2. Issue Triage Agent

一个 GitHub issue 分类 agent。

输入：

```text
issue title
issue body
repo metadata
```

输出：

```text
label: bug / feature / question / docs
priority: low / medium / high
next_action
```

可以模拟工具调用：

```text
search_similar_issues
infer_owner
assign_label
```

第一版可以先 dry-run，不真的改 GitHub。

### 3. Tracing SDK

提供 Python SDK，记录 agent 每一步状态变化。

示例接口：

```python
with trace.step("retrieve_docs"):
    trace.log_state(before=state_before)
    trace.log_event({"type": "retrieval", "chunks": chunks})
    trace.log_decision({"next_action": "answer", "reason_tags": ["has_evidence"]})
    trace.log_state(after=state_after)
```

每一步保存：

```text
run_id
step_id
state_before
event / tool_call / retrieval
decision
reason_tags
state_after
latency
tokens
cost
```

### 4. Replay

保存一次 agent run 后，可以重放同一个 case。

用途：

```text
换 prompt 后再跑
换模型后再跑
mock tool result 后复现 bug
```

第一版可以支持：

```text
replay input
replay retrieved context
replay mocked tool outputs
```

### 5. Diff

对比两个 run：

```text
final output 是否变化
tool calls 是否变化
retrieved chunks 是否变化
状态转移路径是否变化
cost / latency 是否变化
eval pass/fail 是否变化
```

示例：

```text
prompt_v1: retrieve -> answer
prompt_v2: retrieve -> ask_clarification -> answer

diff:
- 多了一步 ask_clarification
- 少引用了 doc_003
- latency +18%
- groundedness 从 pass 变成 fail
```

### 6. JSONL Eval Suite

用 JSONL 写回归测试用例。

示例：

```json
{
  "case_id": "docs_qa_001",
  "agent": "docs_qa",
  "input": {
    "question": "How do I configure the database?"
  },
  "expected": {
    "required_citations": ["docs/config.md"],
    "required_keywords": ["DATABASE_URL"],
    "forbidden_keywords": ["I don't know"],
    "max_latency_ms": 5000
  }
}
```

Issue triage 示例：

```json
{
  "case_id": "issue_bug_001",
  "agent": "issue_triage",
  "input": {
    "title": "App crashes when uploading large files",
    "body": "The upload page freezes after selecting a 2GB file."
  },
  "expected": {
    "label": "bug",
    "priority": "high",
    "required_tool_calls": ["search_similar_issues"],
    "forbidden_tool_calls": ["assign_owner_without_confirmation"]
  }
}
```

### 7. Safety Checks

第一版做轻量安全检查：

```text
PII redaction
forbidden keyword check
forbidden tool call check
max tool calls
approval required tools
```

例如：

```yaml
tools:
  assign_owner:
    mode: dry_run
    approval_required: true
  delete_issue:
    mode: forbidden
```

### 8. Dashboard

Web 页面展示：

```text
run 列表
单次 run trace timeline
每一步 state before/after
tool calls
retrieved chunks
eval pass/fail
run diff
eval report
```

第一版 UI 简单即可，重点是信息密度和可调试性。

## 技术栈

建议：

```text
Python
FastAPI
SQLite
Jinja2 或简单 HTML/JS
pytest
GitHub Actions
OpenAI-compatible LLM API
```

可选：

```text
React
SQLAlchemy
OpenTelemetry export
LangChain adapter
LlamaIndex adapter
```

第一版不建议引入太多框架，重点是把核心 eval / trace / replay 跑通。

## 项目目录建议

```text
agent-reliability-lab/
  agents/
    docs_qa_agent.py
    issue_triage_agent.py
  tracing/
    sdk.py
    store.py
    diff.py
    replay.py
  evals/
    cases/
      docs_qa.jsonl
      issue_triage.jsonl
    runner.py
    metrics.py
  safety/
    pii_redactor.py
    tool_policy.py
  app/
    main.py
    web/
      index.html
      app.js
      styles.css
  reports/
  tests/
  README.md
  requirements.txt
```

## 两周 MVP 路线

### 第 1 阶段：核心可运行

- FastAPI 项目骨架。
- SQLite run store。
- Tracing SDK。
- Docs QA Agent。
- 10 条 docs QA eval cases。
- CLI eval runner。
- Markdown report。

验收标准：

```text
可以运行 docs QA agent
可以保存 trace
可以跑 JSONL eval
可以输出 pass/fail report
```

### 第 2 阶段：agent 能力补全

- Issue Triage Agent。
- 模拟 tool calls。
- tool policy dry-run。
- PII redactor。
- 10 条 issue triage eval cases。

验收标准：

```text
两个 agent 都能跑
工具调用被记录
违规工具调用能被拦截或标记
```

### 第 3 阶段：可靠性工具

- Replay。
- Run diff。
- Dashboard。
- GitHub Actions。

验收标准：

```text
可以对比 prompt v1/v2
可以查看状态转移差异
CI 能自动跑 eval cases
README 有截图或 GIF
```

## 简历写法

英文：

```text
Built Agent Reliability Lab, a lightweight evaluation and observability toolkit for tool-using LLM agents. Implemented two demo agents (RAG-based Docs QA and GitHub issue triage), a Python tracing SDK, SQLite-backed run store, replay/diff engine, JSONL regression suite, and CI reports tracking tool accuracy, groundedness, latency, cost, and safety violations.
```

中文：

```text
实现 Agent Reliability Lab：面向工具调用型 LLM Agent 的评估与可观测性工具。构建 Docs QA RAG Agent 和 GitHub Issue Triage Agent，支持 tracing SDK、运行回放、prompt/model diff、JSONL 回归测试和 CI 报告，统计工具调用准确率、groundedness、延迟、成本和安全违规。
```

## README 应该展示什么

README 不要只写功能列表，要展示结果：

```text
1. 架构图
2. 快速启动命令
3. 一个 trace 截图
4. 一个 diff 截图
5. 一张 eval report 表
6. GitHub Actions badge
7. 10-20 条公开 eval cases
8. 设计取舍：为什么做 trace/replay/regression
```

## 项目亮点

这个项目的亮点不是“调用了大模型”，而是：

```text
把 agent 行为变成可记录、可回放、可对比、可回归测试的工程对象。
```

这比普通聊天 demo 更接近真实 agent 实习工作。

