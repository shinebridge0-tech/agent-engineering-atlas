---
id: bounded-tool-retry
schema_version: '1.0'
revision: 1
locale: zh-CN
title: 工具预算与可诊断终止
problem_cluster: safety
tags:
- safety
- 工具
- 预算
- 重试
- 安全
- tool
- budget
- retry
aliases:
- 工具
- 预算
- 重试
- 安全
- tool
- budget
- retry
problem: Agent 工具失败重试如何限制预算并避免无限调用？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements: []
required_components: []
approach: 由执行层维护总调用预算和允许重试的错误集合；检查次数耗尽时终止，授权失败不重试，写入重试还需单独幂等条件。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 总预算需跨并发统一计数
- 进程重启的预算持久化不在当前演示中
failure_modes: &id001
- 每个重试重新清零总预算
- 所有异常都自动重试外部写入
not_applicable: *id001
implementation_steps:
- 每个实际执行在调用前计入预算
- 授权失败立即终止
- 仅允许分类后的可重试错误
- 预算耗尽保留原因供人工处理
validation_plan:
- 预算耗尽不产生新副作用
- 并发调用不超预算
- 未授权工具不能靠重试获得权限
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: bounded-tool-retry-fact
  text: run_with_retry 根据匹配 policy 判断异常是否重试，并在 attempts 达到 max_attempts 后抛出异常。
  kind: source_fact
  evidence_ids:
  - langgraph-retry
- claim_id: bounded-tool-retry-inference
  text: 节点 max_attempts 不自动等价整条 Agent 流程的总工具预算；总预算和授权拒绝策略需在执行层明确。
  kind: inference
  evidence_ids: &id002
  - langgraph-retry
- claim_id: bounded-tool-retry-recommendation
  text: 由执行层维护总调用预算和允许重试的错误集合；检查次数耗尽时终止，授权失败不重试，写入重试还需单独幂等条件。
  kind: recommendation
  evidence_ids: *id002
sources:
- source_id: langgraph-retry
  source_type: code
  url: https://raw.githubusercontent.com/langchain-ai/langgraph/6aa0afba682b0308fbcace31f66fb532978d4dca/libs/langgraph/langgraph/pregel/_retry.py
  repo: langchain-ai/langgraph
  revision: 6aa0afba682b0308fbcace31f66fb532978d4dca
  path: libs/langgraph/langgraph/pregel/_retry.py
  symbol: run_with_retry
  lines: 573-684
  observed_at: '2026-10-10'
  title: run_with_retry
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 667a74090e23fda724e74ad377586e32325510cdd9042d320d60306f783f0a9d
  mutable: false
review:
  status: source_checked
  reviewer: null
  at: '2026-10-10'
  scope: AI self-check of named symbols and claim mapping; not independent review
validation:
  status: not_run
  environment: null
  command: null
  result: null
freshness:
  status: current
  reason: 源码已按固定 commit 核验；适用发布版本未知
  updated_at: '2026-10-10'
contributors: []
ai_assistance: true
---

## 使用边界

由执行层维护总调用预算和允许重试的错误集合；检查次数耗尽时终止，授权失败不重试，写入重试还需单独幂等条件。

没有运行上游项目；版本适配与业务安全条件需要在目标环境验证。
