---
id: tool-allowlist
schema_version: '1.0'
revision: 1
locale: zh-CN
title: 工具调用前：白名单与参数授权
problem_cluster: safety
tags:
- safety
- 工具
- 授权
- 参数
- 安全
- tool
- authorization
- security
aliases:
- 工具
- 授权
- 参数
- 安全
- tool
- authorization
- security
problem: 如何拒绝未授权工具和越界参数？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements: []
required_components: []
approach: 执行前从可信配置解析工具白名单并做严格参数校验与业务授权；工具描述、JSON Schema 与模型输出都不能替代执行层授权。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 规则需要与业务权限同步维护
- 不是通用不可信代码沙箱
failure_modes: &id001
- 把模型工具选择当授权
- 只验证 Schema 结构不验证参数实例
not_applicable: *id001
implementation_steps:
- 从可信配置注册可执行工具
- 拒绝未知工具和额外参数
- 对参数值作范围与主体授权
- 通过后才调用本地实现
validation_plan:
- 未知工具拒绝且副作用为零
- 越界项目参数拒绝
- 检索文本要求调用其他工具也拒绝
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: tool-allowlist-fact
  text: Tool 初始化用 Draft202012Validator.check_schema 检查参数 Schema；invoke 中调用 self.function(**kwargs)。
  kind: source_fact
  evidence_ids:
  - haystack-tool
- claim_id: tool-allowlist-inference
  text: 该处的 Schema 定义检查不能证明运行时参数或调用者授权已通过；应在实际调用前增加应用侧门禁。
  kind: inference
  evidence_ids: &id002
  - haystack-tool
- claim_id: tool-allowlist-recommendation
  text: 执行前从可信配置解析工具白名单并做严格参数校验与业务授权；工具描述、JSON Schema 与模型输出都不能替代执行层授权。
  kind: recommendation
  evidence_ids: *id002
sources:
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

执行前从可信配置解析工具白名单并做严格参数校验与业务授权；工具描述、JSON Schema 与模型输出都不能替代执行层授权。

没有运行上游项目；版本适配与业务安全条件需要在目标环境验证。
