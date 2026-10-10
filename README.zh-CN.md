# Agent Engineering Atlas · Agent 工程经验库与决策工作台

[English](README.md)。Agent 工程实践图谱，Alpha v0.1.0-alpha.1。维护署名 [@shinebridge0-tech](https://github.com/shinebridge0-tech)；[源码](https://github.com/shinebridge0-tech/agent-engineering-atlas)、[反馈](https://github.com/shinebridge0-tech/agent-engineering-atlas/issues)、[版本](https://github.com/shinebridge0-tech/agent-engineering-atlas/releases)。

问题 + 项目约束 → 候选 → 硬冲突排除 → 比较 → 查看证据 → Markdown / JSON 导出。
基础功能无需模型 key，准备完依赖与内容后可以断网运行。界面明确采用本地规则/关键词辅助，不提供模型聊天或外部工具写入。

## 准备与启动（Windows，已验证路径含空格）

已有 Python 3.11、Node 24（本次实际 3.11.9 / 24.18.0）；不要自动安装系统运行时。
在 PowerShell 进入本项目目录：

```powershell
# Enter the extracted source directory / 进入解压后的源码目录
Set-Location '<your extracted source directory>'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --cache-dir .local/pip-cache -r requirements.lock.txt
Push-Location web
npm ci --cache ../.local/npm-cache
npm run build
Pop-Location
.\.venv\Scripts\python.exe -m backend validate
.\.venv\Scripts\python.exe -m backend rebuild
.\.venv\Scripts\python.exe -m scripts.serve
```

打开 [本地工作台](http://127.0.0.1:18765)。服务仅绑定 127.0.0.1，前端由同一个后端提供。
保持启动终端打开，按 **Ctrl+C** 正常停止；再次运行最后一条命令重启。
端口不可用时拒绝启动，不会终止占用者、不修改防火墙/执行策略。8765 在本机绑定被拒绝，因此采用已验证的 18765。
后台启停方案被平台自动审批拒绝，交付采用前台生命周期，不需要额外权限。
不运行 vite 开发服务器作为正式验收入口，避免端口/Origin 不一致。

## 最短人工验收

1. 保留默认“审批与宕机恢复后避免重复工单”问题；问题簇选“状态与恢复”。
2. 先将要求人工审批选为是，确认项目政策；幂等能力依次选未知/支持/不支持并计算，查看稳定键方案从待核验 → 条件已满足 → 已排除。
3. 禁止新增组件填写 sqlite，再计算；相关持久化方案必须被排除。
4. 选 2–3 个未排除方案比较；打开证据，核对 source_fact/inference/recommendation、commit、路径、符号和日期。
5. 下载 Markdown 与 JSON，检查问题、约束、状态、未知、实施类别、验证、回退和来源。输入改动后导出会禁用，必须重新计算。
6. 案例库筛选/贡献入口可用；问题换成“稀土矿藏地层采样”应报告证据不足。
7. Ctrl+C → 重启 → 刷新。案例/索引恢复；私有问题输入和比较选择不持久化。

## 校验与实验

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend tests scripts experiments
.\.venv\Scripts\python.exe -m scripts.run_experiments
.\.venv\Scripts\python.exe -m scripts.evaluate
Push-Location web
npm run build
npm run lint
npm test
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD\..\.local\browsers"
npx playwright install chromium
# 在另一终端启动项目后：
npx playwright test
Pop-Location
```

依赖锁：requirements.lock.txt / web/package-lock.json。单浏览器缓存、数据库、报告均在 .local（忽略）。
实验输出 .local/experiment-results.json；冻结评测输出 .local/evaluation.json；浏览器截图 .local/workbench.png / mobile.png。
最新实际命令与结果见 [STATUS](docs/ALPHA_PUBLIC_SUMMARY.md) 与 [验证报告](docs/ALPHA_PUBLIC_SUMMARY.md)。

## 内容与边界

content/cases/*.md 为 Markdown + YAML 真源，SQLite 是可删除重建派生物。更改后 validate/rebuild 并刷新；坏文件不会覆盖旧可用索引，启动旧索引时 health 会显示诊断。
检索使用双语 aliases、英文词边界和中文短词回退；检测 FTS5 能力但不依赖它排序。分数不是可信概率。
明确硬冲突优先排除，关键未知只判 conditional，没有可支持候选就显示证据不足。无可比延迟证据时不判满足。

10 张卡：恢复 4 / 检索 3 / 安全 3；source_checked 10 / draft 0 / reviewed 0。上游未运行，卡片 validation 均 not_run。两个本项目原创实验的结果单独记录，不升级为上游或生产验证。
来源许可证未核验：只保留元数据、链接与原创总结，不分发上游可执行实现。官方网页为可变来源；发布版本适配仍为 unknown。

固定的 12 题仅为自建回归集，不是独立盲测。付费模型对照未执行；项目模型 API 调用 0、费用 0。
不上传私有资料、不遥测、不扫描其他项目、不执行外部仓库代码、不包含模型网关或多 Agent 管理平台。
实际 Windows symlink 创建测试因权限不足跳过；路径穿越与根路径逃逸校验有实现和测试。跨平台命令未在 Linux/macOS 运行。

协作规则见 CONTRIBUTING.md / SECURITY.md / CODE_OF_CONDUCT.md。CI 检查推送的固定提交，不自动发布；实际结果以对应提交的 Actions 记录为准。独立人工内容审核仍未执行。

## Alpha v0.1.0-alpha.1

Software/original executable examples: Apache-2.0; original explanatory content: CC BY 4.0. [License scope](docs/LICENSING.md).Enter your extracted source directory instead of the author's drive. Dependencies are not bundled; initial pip/npm installation needs registry access or populated caches. Runtime needs no model key. 不声称安装全过程无网络。

Approval means project policy, not actual tool authorization or proof of an approval service. With approval unknown and idempotency yes, stable-idempotency remains conditional; inspect missing approval confirmation. 明确确认政策后重查；输入变化禁用导出，索引内容变化使旧导出409，必须重新查询。Compare two non-excluded cards, inspect evidence and download both Markdown and JSON. 导出保留输入/内容修订、review/validation/freshness和unknown。

Frozen target retrieval 6/6; confirmed applicability 4/6; conditional 2/6 (approval missing); retained old probes 11/13. 显式确认变体单独登记，不替换原冻结输入。10 cards are zh-CN: recovery4/retrieval3/safety3; source_checked/current/not_run10; reviewed0. English queries/aliases work, formal English card translations are absent. Original experiments are local simulations; upstream execution/version compatibility/production validation remain unverified.

Raw snapshots/private reports are excluded from the ZIP; cards retain public URLs, commits, paths, locations, dates and hashes. [Evidence summary](docs/ALPHA_PUBLIC_SUMMARY.md). Browser automation is optional and Chromium installation is a separate download; an authorized browser cache may be selected with PLAYWRIGHT_BROWSERS_PATH. The stale-content browser test needs explicit isolated AGENTATLAS_R1_BROWSER_WORKSPACE and AGENTATLAS_R1_PYTHON, otherwise skips. Manual demonstration uses an existing browser. Same-machine Windows ZIP isolation does not establish independent or Linux/macOS reproduction. Real symlink/junction validation remains unverified.
