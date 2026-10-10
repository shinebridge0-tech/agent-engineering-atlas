---
id: stable-idempotency
schema_version: '1.0'
revision: 1
locale: zh-CN
title: 稳定业务幂等键 + 接收方持久化去重
problem_cluster: recovery
tags:
- recovery
- 工单
- 幂等
- 恢复
- ticket
- idempotency
- recovery
aliases:
- 工单
- 幂等
- 恢复
- ticket
- idempotency
- recovery
problem: 审批、宕机和并发重试后如何避免重复创建工单？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements:
- key: idempotency
  value: 'yes'
  critical: true
- key: approval
  value: 'yes'
  critical: true
required_components:
- sqlite
approach: 每个逻辑业务操作复用同一幂等键；接收方用持久化唯一约束原子地保存键与工单。审批通过后执行，未知结果用同一键查询或重试。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 需要接收方支持持久化幂等契约
- 键保留期与业务重试窗口必须匹配
failure_modes: &id001
- 接收方无去重契约
- 每次重试重新生成随机键
- 键与副作用不能原子提交
not_applicable: *id001
implementation_steps:
- 在审批前生成并持久化业务操作 ID
- 将审批绑定操作 ID 和参数摘要
- 接收方唯一键与工单在同一事务提交
- 重放复用原键并核对参数一致
validation_plan:
- 成功后记录丢失再重试仅产生一张工单
- 并发请求复用同键仅产生一张工单
- 同键不同参数必须拒绝
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: stable-idempotency-fact
  text: interrupt 恢复从节点起点重新执行，并要求 checkpointer。
  kind: source_fact
  evidence_ids:
  - langgraph-types
- claim_id: stable-idempotency-inference
  text: 节点恢复和重试会重入调用；检查点本身不能原子覆盖外部服务写入。稳定键的去重依赖接收方契约，不能由 LangGraph 自动保证。
  kind: inference
  evidence_ids: &id002
  - langgraph-types
  - langgraph-retry
- claim_id: stable-idempotency-recommendation
  text: 每个逻辑业务操作复用同一幂等键；接收方用持久化唯一约束原子地保存键与工单。审批通过后执行，未知结果用同一键查询或重试。
  kind: recommendation
  evidence_ids: *id002
sources:
- source_id: langgraph-types
  source_type: code
  url: https://raw.githubusercontent.com/langchain-ai/langgraph/6aa0afba682b0308fbcace31f66fb532978d4dca/libs/langgraph/langgraph/types.py
  repo: langchain-ai/langgraph
  revision: 6aa0afba682b0308fbcace31f66fb532978d4dca
  path: libs/langgraph/langgraph/types.py
  symbol: interrupt
  lines: 903-929
  observed_at: '2026-10-10'
  title: interrupt
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 062583a1c0af9833477935a9a78d336408cc9a33c425722a1191e000d032107a
  mutable: false
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

每个逻辑业务操作复用同一幂等键；接收方用持久化唯一约束原子地保存键与工单。审批通过后执行，未知结果用同一键查询或重试。

来源事实、推断与建议见 front matter claims；没有生产保证。
