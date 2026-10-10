# Contributing / 贡献

Maintainer: @shinebridge0-tech. Submit ordinary feedback through [Issues](https://github.com/shinebridge0-tech/agent-engineering-atlas/issues) or [pull requests](https://github.com/shinebridge0-tech/agent-engineering-atlas/pulls).

复制 content/TEMPLATE.md 到 content/cases/<id>.md，替换所有样板内容；模板只展示字段结构，不能原样声明为已核验案例。

- 真源是 Markdown + YAML。id 与 locale 唯一；跨语言共用逻辑 ID 和 revision。
- 填齐问题、条件、代价、反例、实施与验证。未知版本显式写 unknown。
- 每个 claim 指定 source_fact / inference / recommendation，引用真实 sources ID。
- code 来源必须是实际确认的 commit、路径、符号；网页记录标题/节名、日期、可变属性。
- draft 不计入合格种子卡；source_checked 是来源核验，reviewed 需要真实独立审查；不虚构签名、姓名和复现结果。
- 原创实验只运行经检查的本项目代码；外部与社区代码不自动执行。
- AI assistance 应准确标记，贡献者承担来源与权利核对责任；不自动批量合并。

无模型 key 的本地验证（项目根目录）：

```powershell
.\.venv\Scripts\python.exe -m backend validate
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m backend rebuild
```

有效例：tests/fixtures/valid.md；故意无效例：tests/fixtures/invalid.md，仅供拒绝测试。
字段模型与按来源类型约束：backend/content.py；完整 JSON Schema：docs/CASE_SCHEMA.json。
重建失败保留旧索引。重建后刷新页面，导出内容必须反映修订。
软件与原创可执行样例 Apache-2.0，原创解释性内容 CC BY 4.0；范围见 docs/LICENSING.md。第三方保持原许可。

## Three entry points / 三类入口

- Problem lead / 问题线索：.github/ISSUE_TEMPLATE/problem-lead.md，问题、非敏感约束、公开定位、未知；线索不直接成为推荐。
- Case correction / 案例修正：.github/ISSUE_TEMPLATE/case-correction.md，案例/revision/claim ID、原断言、修正依据、引用权利。
- Reproduction or counterexample / 复现或反例：.github/ISSUE_TEMPLATE/reproduction.md，固定环境、命令、输入、实际结果、未执行项与边界。

Security reports use GitHub Private Vulnerability Reporting; see SECURITY.md. AI assistance is allowed and disclosed; submitters verify sources, claims, rights and actual results. Never automatically execute contributed experiments or merge submissions.

隔离复制案例，编辑正文，运行 `python -m scripts.validate_content <isolated case directory>`；通过 `backend.indexing.rebuild(root=..., db=...)` 重建隔离索引并 `read_cards(db=...)` 查看。基础回归 `python -m pytest tests/test_m0.py tests/test_content_index.py -q`。有效/故意无效fixture只证明结构校验，不证明独立来源审核。
