---
id: hybrid-retrieval
schema_version: '1.0'
revision: 2
locale: zh-CN
title: 关键词与向量候选融合：保留分支证据
problem_cluster: retrieval
tags:
- retrieval
- 检索
- 向量
- 混合
- retrieval
- hybrid
- fusion
aliases:
- 检索
- 向量
- 混合
- retrieval
- hybrid
- fusion
problem: 关键词检索与语义向量检索如何比较并融合？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements:
- key: data_external
  value: 'no'
  critical: true
required_components:
- embedding
approach: 分别获取关键词和本地 embedding 候选，记录来源分支与排名后融合；权限与硬约束再独立判断，融合分数不是可信概率。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 需要本地 embedding 组件及版本验证
- 没有此项目语料的向量检索对照实验
failure_modes: &id001
- 禁止新增 embedding 组件
- 没有向量生成环境却声称语义检索已接通
not_applicable: *id001
implementation_steps:
- 先分别评测两个检索分支
- 记录分支排名与案例 ID
- 使用已确认融合策略
- 统一硬约束检查后再展示
validation_plan:
- 同一语料比较关键词和混合召回
- 某分支无结果时可诊断降级
- 硬冲突不能因融合分数变成 compatible
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: hybrid-retrieval-fact
  text: DocumentJoiner 支持 concatenate、merge 和 reciprocal_rank_fusion 模式；run 可以按 score
    排序后应用 top_k。
  kind: source_fact
  evidence_ids:
  - haystack-joiner
- claim_id: hybrid-retrieval-inference
  text: 跨检索器原始分数未必可比，排名融合也不能抵消权限或工程硬约束冲突。
  kind: inference
  evidence_ids: &id002
  - haystack-joiner
  - haystack-embedding
  - haystack-bm25
- claim_id: hybrid-retrieval-recommendation
  text: 分别获取关键词和本地 embedding 候选，记录来源分支与排名后融合；权限与硬约束再独立判断，融合分数不是可信概率。
  kind: recommendation
  evidence_ids: *id002
sources:
- source_id: haystack-joiner
  source_type: code
  url: https://raw.githubusercontent.com/deepset-ai/haystack/c5e13354117d1376d4d8caf0efe77abe80120fc0/haystack/components/joiners/document_joiner.py
  repo: deepset-ai/haystack
  revision: c5e13354117d1376d4d8caf0efe77abe80120fc0
  path: haystack/components/joiners/document_joiner.py
  symbol: DocumentJoiner.run / _rrf
  lines: 146-183; 219-222
  observed_at: '2026-10-10'
  title: DocumentJoiner.run / _rrf
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: e47bdc6ac28e096d597982d366559e80ebe9bd81f395100804572595ff2f4af8
  mutable: false
- source_id: haystack-embedding
  source_type: code
  url: https://raw.githubusercontent.com/deepset-ai/haystack/c5e13354117d1376d4d8caf0efe77abe80120fc0/haystack/components/retrievers/in_memory/embedding_retriever.py
  repo: deepset-ai/haystack
  revision: c5e13354117d1376d4d8caf0efe77abe80120fc0
  path: haystack/components/retrievers/in_memory/embedding_retriever.py
  symbol: InMemoryEmbeddingRetriever.run
  lines: 137-185
  observed_at: '2026-10-10'
  title: InMemoryEmbeddingRetriever.run
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 11ab1491bda559f15bf77c17055771e1279cc60be4397bb954c405e77c461977
  mutable: false
- source_id: haystack-bm25
  source_type: code
  url: https://raw.githubusercontent.com/deepset-ai/haystack/c5e13354117d1376d4d8caf0efe77abe80120fc0/haystack/components/retrievers/in_memory/bm25_retriever.py
  repo: deepset-ai/haystack
  revision: c5e13354117d1376d4d8caf0efe77abe80120fc0
  path: haystack/components/retrievers/in_memory/bm25_retriever.py
  symbol: InMemoryBM25Retriever.run
  lines: 121-157
  observed_at: '2026-10-10'
  title: InMemoryBM25Retriever.run
  license_status: not_checked; metadata and original summary only; no source code
    redistributed
  content_hash: 79c830b6405863e863bcf9786b7611af5984d19188f8653048ddd1bedbd7e465
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

分别获取关键词和本地 embedding 候选，记录来源分支与排名后融合；权限与硬约束再独立判断，融合分数不是可信概率。

没有运行上游项目；版本适配与业务安全条件需要在目标环境验证。

本卡 data_external=no 描述推荐配置无需外传，并非要求用户禁止外传。范围限本地语料、进程内检索与本地向量生成（如需）；不包含远端 embedding、模型生成、遥测或外部存储。上游 in-memory 检索组件接受本地输入；完整部署数据流仍需使用者核验，本卡未运行上游。此为配置限定与工程建议，不是目标项目已具备该能力的证明。
