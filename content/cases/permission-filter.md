---
id: permission-filter
schema_version: '1.0'
revision: 2
locale: zh-CN
title: 检索权限过滤：不能让运行时覆盖安全条件
problem_cluster: retrieval
tags:
- retrieval
- 检索
- 权限
- 过滤
- retrieval
- filter
- permission
aliases:
- 检索
- 权限
- 过滤
- retrieval
- filter
- permission
problem: Agent 检索资料时怎样保持权限过滤不被查询覆盖？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements:
- key: data_external
  value: 'no'
  critical: true
required_components: []
approach: 授权过滤由可信应用构造，和用户查询过滤分开；核验 filter_policy 与组合语义，越权资料不能进入排序或返回给模型。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 需要应用自己的身份与权限依据
- MERGE 的具体组合语义未在此卡运行验证
failure_modes: &id001
- 授权条件来自检索文档或用户 prompt
- 未验证 store 过滤语义就宣称安全
not_applicable: *id001
implementation_steps:
- 在可信层从调用者权限构造过滤
- 禁止不可信输入覆盖安全过滤
- 核验实际 store 对过滤的执行顺序和语义
- 拒绝无法证明权限的检索
validation_plan:
- 用户运行时过滤不能扩大授权集合
- 未授权文档不返回
- 空权限集合返回空结果而非全库
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: permission-filter-fact
  text: BM25 与 embedding retriever 的 filter_policy 文档说明 REPLACE 为默认值、MERGE 合并初始化与运行时过滤；run
    调用 apply_filter_policy。
  kind: source_fact
  evidence_ids:
  - haystack-bm25
  - haystack-embedding
- claim_id: permission-filter-inference
  text: 运行时过滤替换初始化过滤可能改变访问集合，不能把通用组件过滤 API 当作自动成立的授权边界。
  kind: inference
  evidence_ids: &id002
  - haystack-bm25
  - haystack-embedding
- claim_id: permission-filter-recommendation
  text: 授权过滤由可信应用构造，和用户查询过滤分开；核验 filter_policy 与组合语义，越权资料不能进入排序或返回给模型。
  kind: recommendation
  evidence_ids: *id002
sources:
- source_id: haystack-bm25
  source_type: code
  url: https://raw.githubusercontent.com/deepset-ai/haystack/c5e13354117d1376d4d8caf0efe77abe80120fc0/haystack/components/retrievers/in_memory/bm25_retriever.py
  repo: deepset-ai/haystack
  revision: c5e13354117d1376d4d8caf0efe77abe80120fc0
  path: haystack/components/retrievers/in_memory/bm25_retriever.py
  symbol: InMemoryBM25Retriever.__init__ / run
  lines: 61-65; 121-157
  observed_at: '2026-10-10'
  title: InMemoryBM25Retriever.run
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 79c830b6405863e863bcf9786b7611af5984d19188f8653048ddd1bedbd7e465
  mutable: false
- source_id: haystack-embedding
  source_type: code
  url: https://raw.githubusercontent.com/deepset-ai/haystack/c5e13354117d1376d4d8caf0efe77abe80120fc0/haystack/components/retrievers/in_memory/embedding_retriever.py
  repo: deepset-ai/haystack
  revision: c5e13354117d1376d4d8caf0efe77abe80120fc0
  path: haystack/components/retrievers/in_memory/embedding_retriever.py
  symbol: InMemoryEmbeddingRetriever.__init__ / run
  lines: 75-79; 137-185
  observed_at: '2026-10-10'
  title: InMemoryEmbeddingRetriever.run
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 11ab1491bda559f15bf77c17055771e1279cc60be4397bb954c405e77c461977
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

授权过滤由可信应用构造，和用户查询过滤分开；核验 filter_policy 与组合语义，越权资料不能进入排序或返回给模型。

没有运行上游项目；版本适配与业务安全条件需要在目标环境验证。

本卡 data_external=no 描述推荐配置无需外传，并非要求用户禁止外传。范围限本地语料、进程内检索与本地向量生成（如需）；不包含远端 embedding、模型生成、遥测或外部存储。上游 in-memory 检索组件接受本地输入；完整部署数据流仍需使用者核验，本卡未运行上游。此为配置限定与工程建议，不是目标项目已具备该能力的证明。
