---
id: approval-before-effect
schema_version: '1.0'
revision: 1
locale: zh-CN
title: 审批节点与副作用节点分离
problem_cluster: recovery
tags:
- recovery
- 工单
- 审批
- 恢复
- interrupt
- ticket
- checkpoint
aliases:
- 工单
- 审批
- 恢复
- interrupt
- ticket
- checkpoint
problem: 人工中断与宕机恢复如何减少重复工单的重放范围？
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
- key: framework
  value: LangGraph
  critical: true
required_components:
- checkpointer
approach: 先在纯审批节点 interrupt，审批结果校验后进入副作用节点。分离缩小审批重放影响，但副作用节点仍可能重试，必须结合接收方幂等。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 新增持久化 checkpointer
- 版本兼容和会话标识需核验
failure_modes: &id001
- 把 Command(resume=True) 当作完整授权验证
- 缺少稳定键仍宣称不重复
not_applicable: *id001
implementation_steps:
- 审批节点只计算与展示待批准参数
- 持久化检查点和操作 ID
- 校验审批结果再路由到执行节点
- 执行节点仍复用业务幂等键
validation_plan:
- 审批拒绝不执行写入
- 恢复重跑审批节点不产生副作用
- 执行节点崩溃后同键重试
frameworks:
- LangGraph
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: approval-before-effect-fact
  text: interrupt 在节点首次调用时抛出 GraphInterrupt；客户端用 Command(resume=...) 继续，节点从起点执行。
  kind: source_fact
  evidence_ids:
  - langgraph-types
- claim_id: approval-before-effect-inference
  text: 在 interrupt 之前做外部写入会随节点恢复重做；分离节点不会消除发送成功但本地记录未提交的窗口。
  kind: inference
  evidence_ids: &id002
  - langgraph-types
- claim_id: approval-before-effect-recommendation
  text: 先在纯审批节点 interrupt，审批结果校验后进入副作用节点。分离缩小审批重放影响，但副作用节点仍可能重试，必须结合接收方幂等。
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

先在纯审批节点 interrupt，审批结果校验后进入副作用节点。分离缩小审批重放影响，但副作用节点仍可能重试，必须结合接收方幂等。

来源事实、推断与建议见 front matter claims；没有生产保证。
