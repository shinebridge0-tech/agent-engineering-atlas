---
id: reconcile-before-retry
schema_version: '1.0'
revision: 1
locale: zh-CN
title: 无幂等接口：未知结果进入核对队列
problem_cluster: recovery
tags:
- recovery
- 工单
- 恢复
- 重复
- ticket
- reconciliation
- recovery
aliases:
- 工单
- 恢复
- 重复
- ticket
- reconciliation
- recovery
problem: 外部接口不支持幂等时，审批恢复后怎样控制重复工单风险？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements:
- key: idempotency
  value: 'no'
  critical: true
- key: approval
  value: 'yes'
  critical: true
required_components:
- sqlite
approach: 持久化操作意图与发送状态；结果不确定时停止自动重试，人工或可信业务查询核对后再决定。只能控制盲重试，不能承诺 exactly-once。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 需要人工参与，恢复延迟不可预测
- 查询完整性和一致性必须单独验证
failure_modes: &id001
- 要求无人值守且保证不重复
- 将未查到等同未创建
- 未知结果直接盲重试
not_applicable: *id001
implementation_steps:
- 先持久化意图和参数摘要
- 审批绑定意图
- 发送后未知状态进入核对队列
- 核对者确认是否重试并记录理由
validation_plan:
- 注入远端成功但本地未记录的中断后不自动发送第二次
- 不存在可靠查询时明确阻塞
- 人工拒绝后没有副作用
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: reconcile-before-retry-fact
  text: run_with_retry 清理上次任务 writes 并再次调用 task.proc.invoke；达到 max_attempts 后抛出异常。
  kind: source_fact
  evidence_ids:
  - langgraph-retry
- claim_id: reconcile-before-retry-inference
  text: 任务写入清理不是外部工单撤销；发送后断线时存在无法从本地记录判定远端成功的窗口。
  kind: inference
  evidence_ids: &id002
  - langgraph-retry
- claim_id: reconcile-before-retry-recommendation
  text: 持久化操作意图与发送状态；结果不确定时停止自动重试，人工或可信业务查询核对后再决定。只能控制盲重试，不能承诺 exactly-once。
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

持久化操作意图与发送状态；结果不确定时停止自动重试，人工或可信业务查询核对后再决定。只能控制盲重试，不能承诺 exactly-once。

来源事实、推断与建议见 front matter claims；没有生产保证。
