---
id: bound-approval
schema_version: '1.0'
revision: 2
locale: zh-CN
title: 审批绑定操作参数与有效期
problem_cluster: safety
tags:
- safety
- 工具
- 审批
- 过期
- 批准
- tool
- approval
- security
aliases:
- 工具
- 审批
- 过期
- 批准
- tool
- approval
- security
problem: 人工审批恢复后，如何拒绝过期、伪造或被换参的批准？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements:
- key: approval
  value: 'yes'
  critical: true
required_components: []
approach: 可信审批服务签发与工具、主体、业务操作 ID、参数摘要和到期时间绑定的批准；执行前重新校验，模型返回 approve 不构成有效批准。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 需要可信签发与时钟假设
- 一次性批准持久化消费不在当前演示中
failure_modes: &id001
- 允许不可信模型自行签发批准
- 审批 ID 可被跨操作复用
not_applicable: *id001
implementation_steps:
- 规范化参数计算摘要
- 审批包含工具、主体、操作 ID、到期时间
- 执行前验证可信签名和字段一致
- 过期或换参请求拒绝
validation_plan:
- 篡改参数后批准失效
- 过期、伪造及缺失批准无副作用
- 合法批准只允许已绑定操作
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: bound-approval-fact
  text: interrupt 的恢复值由客户端 Command 指定；Tool.invoke 会调用绑定的 function。
  kind: source_fact
  evidence_ids:
  - langgraph-types
  - haystack-tool
- claim_id: bound-approval-inference
  text: 可以恢复执行不等于批准真实有效；恢复值必须经过应用侧参数绑定和有效期校验。
  kind: inference
  evidence_ids: &id002
  - langgraph-types
  - haystack-tool
- claim_id: bound-approval-recommendation
  text: 可信审批服务签发与工具、主体、业务操作 ID、参数摘要和到期时间绑定的批准；执行前重新校验，模型返回 approve 不构成有效批准。
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
- source_id: haystack-tool
  source_type: code
  url: https://raw.githubusercontent.com/deepset-ai/haystack/c5e13354117d1376d4d8caf0efe77abe80120fc0/haystack/tools/tool.py
  repo: deepset-ai/haystack
  revision: c5e13354117d1376d4d8caf0efe77abe80120fc0
  path: haystack/tools/tool.py
  symbol: Tool.__post_init__ / invoke
  lines: 132-136; 274-296
  observed_at: '2026-10-10'
  title: Tool.__post_init__ / invoke
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 30de56c6def6c9859931b6805c23999f2f3807cd716f4e9c1d2cb88a58275c2b
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

可信审批服务签发与工具、主体、业务操作 ID、参数摘要和到期时间绑定的批准；执行前重新校验，模型返回 approve 不构成有效批准。

没有运行上游项目；版本适配与业务安全条件需要在目标环境验证。
