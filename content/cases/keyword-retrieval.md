---
id: keyword-retrieval
schema_version: '1.0'
revision: 2
locale: zh-CN
title: 关键词优先：可解释的本地召回
problem_cluster: retrieval
tags:
- retrieval
- 检索
- 关键词
- 中文
- retrieval
- bm25
- search
aliases:
- 检索
- 关键词
- 中文
- retrieval
- bm25
- search
problem: Agent 如何检索明确术语、符号或错误文本？
context: 本项目原创工程总结；上游源码观察与建议分别标注。未运行上游项目。
preconditions:
- 先确认业务和信任边界
- 下列方案的条件必须由使用者核验
hard_requirements:
- key: data_external
  value: 'no'
  critical: true
required_components: []
approach: 明确术语先做关键词召回，并用本地双语 aliases 与中文短词补足分词；离线运行无需远端 embedding。生产语料效果需要单独评测。
alternatives:
- 比较同问题其他卡片；没有满足约束的方案时停止推荐
tradeoffs:
- 同义表达召回有限
- 需要维护 aliases 和回归集
failure_modes: &id001
- 要求语义近义召回且无词汇重合
- 把相关分数当正确概率
not_applicable: *id001
implementation_steps:
- 保存可追溯案例内容与双语 aliases
- 参数化查询并限制长度
- 验证中文连续词和英文缩写
- 约束过滤在召回之后独立执行
validation_plan:
- 中文短词检索与英文术语召回
- 特殊字符不触发 SQL/FTS 注入
- 空问题拒绝，无匹配明确不足
frameworks:
- neutral
tested_versions:
- unknown
applicable_version_range: unknown; observations pinned to source commit, not a tested
  release range
claims:
- claim_id: keyword-retrieval-fact
  text: InMemoryBM25Retriever.run 接收 query、filters 和 top_k，经 apply_filter_policy 后调用
    document_store.bm25_retrieval。
  kind: source_fact
  evidence_ids:
  - haystack-bm25
- claim_id: keyword-retrieval-inference
  text: 关键词召回可以保留术语匹配的可解释性，但英文分词行为不能直接外推中文短词召回。
  kind: inference
  evidence_ids: &id002
  - haystack-bm25
- claim_id: keyword-retrieval-recommendation
  text: 明确术语先做关键词召回，并用本地双语 aliases 与中文短词补足分词；离线运行无需远端 embedding。生产语料效果需要单独评测。
  kind: recommendation
  evidence_ids: *id002
sources:
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

明确术语先做关键词召回，并用本地双语 aliases 与中文短词补足分词；离线运行无需远端 embedding。生产语料效果需要单独评测。

没有运行上游项目；版本适配与业务安全条件需要在目标环境验证。

本卡 data_external=no 描述推荐配置无需外传，并非要求用户禁止外传。范围限本地语料、进程内检索与本地向量生成（如需）；不包含远端 embedding、模型生成、遥测或外部存储。上游 in-memory 检索组件接受本地输入；完整部署数据流仍需使用者核验，本卡未运行上游。此为配置限定与工程建议，不是目标项目已具备该能力的证明。
